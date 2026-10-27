/**
 * Acceso seguro a localStorage (puede fallar en modo privado, cuotas o políticas del navegador).
 *
 * Se guardan dos claves:
 *  - `psitwin.token`  → JWT.
 *  - `psitwin.sesion` → JSON con los datos de la sesión que devuelve el login (rol, empresa, operario,
 *    debe_cambiar_password). Se escribe junto con el token y se borra con él.
 */
const TOKEN_KEY = 'psitwin.token'
const SESION_KEY = 'psitwin.sesion'

/** Evento que se emite en window cuando el token o la sesión cambian desde fuera de React (ej. 401 en el cliente). */
export const TOKEN_CHANGE_EVENT = 'psitwin:token-change'

function safeGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function safeSet(key: string, value: string | null): void {
  try {
    if (value === null) window.localStorage.removeItem(key)
    else window.localStorage.setItem(key, value)
  } catch {
    /* almacenamiento no disponible: la sesión vivirá solo en memoria */
  }
}

let memoryToken: string | null = null
let memorySesion: string | null = null

const emitir = () => window.dispatchEvent(new Event(TOKEN_CHANGE_EVENT))

export function getToken(): string | null {
  return safeGet(TOKEN_KEY) ?? memoryToken
}

/** JSON crudo de la sesión (lo interpreta `SessionContext`). */
export function getSesionRaw(): string | null {
  return safeGet(SESION_KEY) ?? memorySesion
}

/** Guarda (o borra, con `null`) el token. Al borrarlo también se borran los datos de sesión. */
export function setToken(token: string | null): void {
  memoryToken = token
  safeSet(TOKEN_KEY, token)
  if (token === null) {
    memorySesion = null
    safeSet(SESION_KEY, null)
  }
  emitir()
}

/** Guarda token + datos de sesión de una sola vez (un único evento de cambio). */
export function setSesion(token: string, sesion: Record<string, unknown>): void {
  const raw = JSON.stringify(sesion)
  memorySesion = raw
  safeSet(SESION_KEY, raw)
  memoryToken = token
  safeSet(TOKEN_KEY, token)
  emitir()
}

/** Mezcla campos en los datos de sesión guardados (ej. `{ debe_cambiar_password: false }`). */
export function patchSesion(patch: Record<string, unknown>): void {
  let actual: Record<string, unknown> = {}
  try {
    const raw = getSesionRaw()
    if (raw) actual = JSON.parse(raw) as Record<string, unknown>
  } catch {
    actual = {}
  }
  const raw = JSON.stringify({ ...actual, ...patch })
  if (raw === getSesionRaw()) return
  memorySesion = raw
  safeSet(SESION_KEY, raw)
  emitir()
}

export function clearToken(): void {
  setToken(null)
}

export const STORAGE_TOKEN_KEY = TOKEN_KEY
export const STORAGE_SESION_KEY = SESION_KEY
