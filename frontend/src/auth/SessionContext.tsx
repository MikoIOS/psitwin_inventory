/**
 * Sesión del usuario autenticado (EMPRESA, OPERARIO o PROVEEDOR). Guarda el token y los datos del login
 * (rol, empresa, operario, proveedor, debe_cambiar_password) en localStorage (vía `lib/storage`) y los expone a React.
 *
 * - `useSession()` → { token, isAuthenticated, rol, empresa, operario, proveedor, debeCambiarPassword,
 *                      iniciarSesion(token, datos), actualizarSesion(patch), cerrarSesion() }
 * - El cliente HTTP también puede cambiar la sesión (401 → la borra; 403 PASSWORD_CHANGE_REQUIRED →
 *   marca `debe_cambiar_password`); el contexto se entera por evento.
 * - Rol: el guardado en la sesión; si no hay (sesión antigua), el claim `rol` del JWT; si tampoco, EMPRESA.
 */
import { useQueryClient } from '@tanstack/react-query'
import { createContext, use, useCallback, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import type { Empresa, Operario, Proveedor, Rol } from '@/api/types'
import {
  getSesionRaw,
  getToken,
  patchSesion,
  setSesion,
  setToken,
  STORAGE_SESION_KEY,
  STORAGE_TOKEN_KEY,
  TOKEN_CHANGE_EVENT,
} from '@/lib/storage'

export interface DatosSesion {
  rol: Rol
  empresa: Empresa | null
  operario: Operario | null
  proveedor: Proveedor | null
  debeCambiarPassword: boolean
}

interface SessionValue extends DatosSesion {
  token: string | null
  isAuthenticated: boolean
  iniciarSesion: (token: string, datos?: Partial<DatosSesion>) => void
  actualizarSesion: (patch: Partial<DatosSesion>) => void
  cerrarSesion: () => void
}

const SessionContext = createContext<SessionValue | null>(null)

function subscribe(onChange: () => void) {
  const onStorage = (e: StorageEvent) => {
    if (e.key === null || e.key === STORAGE_TOKEN_KEY || e.key === STORAGE_SESION_KEY) onChange()
  }
  window.addEventListener(TOKEN_CHANGE_EVENT, onChange)
  window.addEventListener('storage', onStorage) // sincroniza entre pestañas
  return () => {
    window.removeEventListener(TOKEN_CHANGE_EVENT, onChange)
    window.removeEventListener('storage', onStorage)
  }
}

/** Payload de un JWT sin verificar (solo para leer el claim `rol` de sesiones antiguas). */
export function leerClaimsJwt(token: string | null): Record<string, unknown> | null {
  if (!token) return null
  const parte = token.split('.')[1]
  if (!parte) return null
  try {
    const b64 = parte.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(parte.length / 4) * 4, '=')
    const json = decodeURIComponent(
      Array.from(atob(b64), (c) => `%${c.charCodeAt(0).toString(16).padStart(2, '0')}`).join(''),
    )
    const claims: unknown = JSON.parse(json)
    return typeof claims === 'object' && claims !== null ? (claims as Record<string, unknown>) : null
  } catch {
    return null
  }
}

function esRol(v: unknown): v is Rol {
  return v === 'EMPRESA' || v === 'OPERARIO' || v === 'PROVEEDOR'
}

function parsearSesion(token: string | null, raw: string | null): DatosSesion {
  let datos: Record<string, unknown> = {}
  try {
    if (raw) datos = JSON.parse(raw) as Record<string, unknown>
  } catch {
    datos = {}
  }
  const claimRol = leerClaimsJwt(token)?.rol
  const rol: Rol = esRol(datos.rol) ? datos.rol : esRol(claimRol) ? claimRol : 'EMPRESA'
  return {
    rol,
    empresa: (datos.empresa as Empresa | null | undefined) ?? null,
    operario: (datos.operario as Operario | null | undefined) ?? null,
    proveedor: (datos.proveedor as Proveedor | null | undefined) ?? null,
    debeCambiarPassword: rol !== 'EMPRESA' && datos.debe_cambiar_password === true,
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const token = useSyncExternalStore(subscribe, getToken, () => null)
  const sesionRaw = useSyncExternalStore(subscribe, getSesionRaw, () => null)

  const iniciarSesion = useCallback(
    (nuevo: string, datos: Partial<DatosSesion> = {}) => {
      queryClient.clear()
      const claimRol = leerClaimsJwt(nuevo)?.rol
      setSesion(nuevo, {
        rol: datos.rol ?? (esRol(claimRol) ? claimRol : 'EMPRESA'),
        empresa: datos.empresa ?? null,
        operario: datos.operario ?? null,
        proveedor: datos.proveedor ?? null,
        debe_cambiar_password: datos.debeCambiarPassword ?? false,
      })
    },
    [queryClient],
  )

  const actualizarSesion = useCallback((patch: Partial<DatosSesion>) => {
    const out: Record<string, unknown> = {}
    if ('empresa' in patch) out.empresa = patch.empresa
    if ('rol' in patch) out.rol = patch.rol
    if ('operario' in patch) out.operario = patch.operario
    if ('proveedor' in patch) out.proveedor = patch.proveedor
    if ('debeCambiarPassword' in patch) out.debe_cambiar_password = patch.debeCambiarPassword
    patchSesion(out)
  }, [])

  const cerrarSesion = useCallback(() => {
    setToken(null)
    queryClient.clear()
  }, [queryClient])

  const value = useMemo<SessionValue>(() => {
    const datos = parsearSesion(token, sesionRaw)
    return { ...datos, token, isAuthenticated: token !== null, iniciarSesion, actualizarSesion, cerrarSesion }
  }, [token, sesionRaw, iniciarSesion, actualizarSesion, cerrarSesion])

  return <SessionContext value={value}>{children}</SessionContext>
}

export function useSession(): SessionValue {
  const ctx = use(SessionContext)
  if (!ctx) throw new Error('useSession debe usarse dentro de <SessionProvider>')
  return ctx
}
