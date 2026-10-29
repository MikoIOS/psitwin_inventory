/**
 * Cliente HTTP de PsiTwin: wrapper de fetch con Bearer token, parseo de errores y manejo global de:
 *  - 401 → limpia la sesión y redirige a /login.
 *  - 403 con `code = PASSWORD_CHANGE_REQUIRED` → marca la sesión (`debe_cambiar_password`); los guards
 *    llevan al operario / proveedor a /cambiar-password. NO cierra la sesión.
 *  - cualquier otro 403 → solo lanza el ApiError ("sin permiso"); la pantalla lo muestra (toast / ErrorState).
 *
 * Uso: `api.get<Almacen[]>('/almacenes')`, `api.post<Zona>('/zonas', body)`.
 * NO llamar a fetch directamente desde componentes: usar las funciones de `src/api/<recurso>.ts`.
 */
import { clearToken, getToken, patchSesion } from '@/lib/storage'

export const API_URL: string = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/+$/, '')

/** Error de FastAPI 422: `{ detail: [{ loc: ['body', 'campo'], msg, type }] }`. */
interface FastApiValidationItem {
  loc?: (string | number)[]
  msg?: string
  type?: string
}

const MENSAJES_POR_STATUS: Record<number, string> = {
  0: 'No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.',
  400: 'La solicitud no es válida.',
  401: 'Tu sesión expiró. Inicia sesión nuevamente.',
  403: 'No tienes permiso para realizar esta acción.',
  404: 'No se encontró el registro solicitado.',
  409: 'La operación no está permitida por una regla del sistema.',
  422: 'Revisa los datos del formulario.',
  500: 'Ocurrió un error inesperado en el servidor. Inténtalo más tarde.',
}

/** Traducciones de los mensajes más comunes de Pydantic/FastAPI. */
const TRADUCCIONES_PYDANTIC: [RegExp, string | ((m: RegExpMatchArray) => string)][] = [
  [/^Field required$/i, 'Campo obligatorio'],
  [/^Input should be a valid number.*$/i, 'Debe ser un número válido'],
  [/^Input should be a valid integer.*$/i, 'Debe ser un número entero'],
  [/^Input should be a valid string$/i, 'Debe ser un texto'],
  [/^Input should be a valid boolean.*$/i, 'Debe ser verdadero o falso'],
  [/^Input should be a valid UUID.*$/i, 'Identificador no válido'],
  [/^Input should be a valid datetime.*$/i, 'Fecha no válida'],
  [/^value is not a valid email address.*$/i, 'Correo electrónico no válido'],
  [/^Input should be greater than or equal to (.+)$/i, (m) => `Debe ser mayor o igual a ${m[1]}`],
  [/^Input should be greater than (.+)$/i, (m) => `Debe ser mayor que ${m[1]}`],
  [/^Input should be less than or equal to (.+)$/i, (m) => `Debe ser menor o igual a ${m[1]}`],
  [/^Input should be less than (.+)$/i, (m) => `Debe ser menor que ${m[1]}`],
  [/^String should have at least (\d+) characters?$/i, (m) => `Debe tener al menos ${m[1]} caracteres`],
  [/^String should have at most (\d+) characters?$/i, (m) => `Debe tener como máximo ${m[1]} caracteres`],
  [/^Input should be (.+)$/i, (m) => `Valor no permitido (${m[1]})`],
]

function traducir(msg: string): string {
  const limpio = msg.replace(/^Value error,\s*/i, '').replace(/^Assertion failed,\s*/i, '')
  for (const [re, rep] of TRADUCCIONES_PYDANTIC) {
    const m = limpio.match(re)
    if (m) return typeof rep === 'string' ? rep : rep(m)
  }
  return limpio
}

export class ApiError extends Error {
  /** Código HTTP (0 = error de red / sin respuesta). */
  readonly status: number
  /** Mensaje legible en español listo para mostrar. */
  readonly detail: string
  /** Errores 422 por campo: `{ nombre_campo: 'mensaje' }` (clave = último segmento de `loc`). */
  readonly fieldErrors: Record<string, string>
  /** Cuerpo crudo de la respuesta (para depuración). */
  readonly body: unknown
  /** Código de error de la API si lo envía (ej. `PASSWORD_CHANGE_REQUIRED`). */
  readonly code: string | null

  constructor(status: number, detail: string, fieldErrors: Record<string, string> = {}, body: unknown = null, code: string | null = null) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.fieldErrors = fieldErrors
    this.body = body
    this.code = code
  }

  get isNetwork() {
    return this.status === 0
  }
  /** 401: sesión inválida/expirada (el cliente ya cerró la sesión). */
  get isUnauthorized() {
    return this.status === 401
  }
  /** 403: sin permiso para este recurso/acción (la sesión sigue activa). */
  get isForbidden() {
    return this.status === 403
  }
  /** 403 del operario / proveedor que aún no cambió su contraseña temporal. */
  get isPasswordChangeRequired() {
    return this.status === 403 && this.code === CODE_PASSWORD_CHANGE_REQUIRED
  }
  /** Errores que el cliente ya gestiona globalmente (401 y cambio de contraseña obligatorio): no mostrar nada. */
  get isHandledGlobally() {
    return this.isUnauthorized || this.isPasswordChangeRequired
  }
  get isNotFound() {
    return this.status === 404
  }
  get isConflict() {
    return this.status === 409
  }
  get isValidation() {
    return this.status === 422
  }
  get isServer() {
    return this.status >= 500
  }
  get hasFieldErrors() {
    return Object.keys(this.fieldErrors).length > 0
  }

  static async fromResponse(res: Response): Promise<ApiError> {
    const body = await readBody(res)
    let rawDetail = isRecord(body) ? body.detail : undefined
    // `code` puede venir junto a `detail` o dentro de él (HTTPException(detail={detail, code})).
    let code: string | null = null
    if (isRecord(body) && typeof body.code === 'string') code = body.code
    if (isRecord(rawDetail)) {
      if (!code && typeof rawDetail.code === 'string') code = rawDetail.code
      rawDetail = rawDetail.detail ?? rawDetail.message ?? rawDetail.msg
    }
    const fieldErrors: Record<string, string> = {}
    let detail = MENSAJES_POR_STATUS[res.status] ?? (res.status >= 500 ? MENSAJES_POR_STATUS[500]! : `Error ${res.status}`)

    if (Array.isArray(rawDetail)) {
      const generales: string[] = []
      for (const item of rawDetail as FastApiValidationItem[]) {
        const msg = traducir(item.msg ?? 'Valor no válido')
        const campo = campoDesdeLoc(item.loc)
        if (campo && !(campo in fieldErrors)) fieldErrors[campo] = msg
        else if (!campo) generales.push(msg)
      }
      if (generales.length > 0) detail = generales.join('. ')
    } else if (typeof rawDetail === 'string' && rawDetail.trim() !== '' && res.status < 500) {
      detail = traducir(rawDetail)
    } else if (typeof body === 'string' && body.trim() !== '' && res.status < 500 && body.length < 300) {
      detail = body
    }

    if (code === 'GOOGLE_NOT_CONFIGURED') detail = 'El acceso con Google aún no está configurado. Contacta al administrador.'
    return new ApiError(res.status, detail, fieldErrors, body, code)
  }
}

export const CODE_PASSWORD_CHANGE_REQUIRED = 'PASSWORD_CHANGE_REQUIRED'

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

/** ['body', 'cantidad'] → 'cantidad'. ['body'] → null (error general del body). */
function campoDesdeLoc(loc: FastApiValidationItem['loc']): string | null {
  if (!loc || loc.length === 0) return null
  const partes = loc.filter((p): p is string => typeof p === 'string' && !['body', 'query', 'path', 'header'].includes(p))
  return partes.at(-1) ?? null
}

async function readBody(res: Response): Promise<unknown> {
  if (res.status === 204) return undefined
  const text = await res.text().catch(() => '')
  if (!text) return undefined
  const type = res.headers.get('content-type') ?? ''
  if (type.includes('json')) {
    try {
      return JSON.parse(text) as unknown
    } catch {
      return text
    }
  }
  return text
}

/* ------------------------------------------------------------------ */

type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, QueryValue>
  /** false = no enviar token ni aplicar la redirección global en 401 (login/registro). */
  auth?: boolean
  /** false = enviar token pero NO cerrar sesión ante 401 (p. ej. contraseña actual incorrecta). */
  logoutOnAuthError?: boolean
  signal?: AbortSignal
}

let redirigiendo = false

/** Limpia la sesión y navega a /login. Recarga completa para vaciar cachés en memoria. */
export function forzarLogout(motivo: 'expirada' | 'prohibido' | 'inactivo' | 'salir' = 'expirada'): void {
  clearToken()
  if (redirigiendo || window.location.pathname === '/login') return
  redirigiendo = true
  const url = motivo === 'salir' ? '/login' : `/login?motivo=${motivo}`
  window.location.assign(url)
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = `${API_URL}${path.startsWith('/') ? path : `/${path}`}`
  if (!query) return url
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  }
  const qs = params.toString()
  return qs ? `${url}?${qs}` : url
}

export async function apiRequest<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, auth = true, logoutOnAuthError = true, signal } = opts
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : null,
      signal: signal ?? null,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError(0, MENSAJES_POR_STATUS[0]!, {}, err)
  }

  if (!res.ok) {
    const error = await ApiError.fromResponse(res)
    if (auth && error.isPasswordChangeRequired) {
      // No se cierra la sesión: los guards llevan al operario a /cambiar-password.
      patchSesion({ debe_cambiar_password: true })
    } else if (auth && logoutOnAuthError && (res.status === 401 || (res.status === 403 && /^not authenticated$/i.test(error.detail)))) {
      // 401 (o el 403 "Not authenticated" de HTTPBearer en FastAPI antiguo) → sesión inválida.
      forzarLogout('expirada')
    } else if (auth && res.status === 403 && /^(operario|proveedor) inactivo$/i.test(error.detail.trim())) {
      // La empresa desactivó la cuenta: su sesión ya no sirve para nada.
      forzarLogout('inactivo')
    }
    if (error.isServer) console.error(`[api] ${method} ${path} → ${res.status}`, error.body)
    throw error
  }

  return (await readBody(res)) as T
}

export const api = {
  get: <T>(path: string, opts?: Omit<RequestOptions, 'method' | 'body'>) => apiRequest<T>(path, { ...opts, method: 'GET' }),
  post: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...opts, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...opts, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...opts, method: 'PATCH', body }),
  delete: <T = void>(path: string, opts?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...opts, method: 'DELETE' }),
}

/** Codifica un segmento de ruta (ids, categorías con espacios, "MAÑANA"...). */
export const seg = (v: string) => encodeURIComponent(v)
