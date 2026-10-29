/**
 * Autenticación: un solo login para EMPRESA, OPERARIO y PROVEEDOR (el registro es solo para empresas).
 *   POST /auth/register · POST /auth/login · GET /auth/me · PATCH /auth/me/password (operario / proveedor)
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useSession, type DatosSesion } from '@/auth/SessionContext'
import { api, ApiError } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { CambiarPasswordBody, Empresa, LoginBody, LoginResponseRaw, MeResponseRaw, RegisterBody } from './types'

function aDatosSesion(raw: MeResponseRaw): DatosSesion {
  const rol = raw.rol === 'OPERARIO' || raw.rol === 'PROVEEDOR' ? raw.rol : 'EMPRESA'
  return {
    rol,
    empresa: raw.empresa ? norm.empresa.one(raw.empresa) : null,
    operario: rol === 'OPERARIO' && raw.operario ? norm.operario.one(raw.operario) : null,
    proveedor: rol === 'PROVEEDOR' && raw.proveedor ? norm.proveedor.one(raw.proveedor) : null,
    debeCambiarPassword: rol !== 'EMPRESA' && raw.debe_cambiar_password === true,
  }
}

export const authApi = {
  resendVerification: (correo: string) => api.post<{ message: string }>('/auth/verification/resend', { correo }, { auth: false }),
  confirmVerification: (token: string) => api.post<{ message: string }>('/auth/verification/confirm', { token }, { auth: false }),
  fromGoogle: (raw: LoginResponseRaw): LoginResult => {
    if (!raw.access_token) throw new ApiError(500, 'El servidor no devolvió la sesión.', {}, raw)
    return { token: raw.access_token, ...aDatosSesion(raw) }
  },
  register: async (body: RegisterBody): Promise<Empresa> =>
    norm.empresa.one(await api.post('/auth/register', body, { auth: false })),

  /** `{ access_token, token_type, rol, empresa, operario, proveedor, debe_cambiar_password }`. */
  login: async (body: LoginBody): Promise<LoginResult> => {
    const raw = await api.post<LoginResponseRaw>('/auth/login', body, { auth: false })
    if (!raw?.access_token) throw new ApiError(500, 'El servidor no devolvió un token de acceso.', {}, raw)
    return { token: raw.access_token, ...aDatosSesion(raw) }
  },
  /** Cualquier rol (permitido también con `debe_cambiar_password`). */
  me: async (): Promise<DatosSesion> => aDatosSesion(await api.get<MeResponseRaw>('/auth/me')),
  /** Solo OPERARIO / PROVEEDOR. Contraseña actual incorrecta → 400 (no cierra la sesión). */
  cambiarPassword: (body: CambiarPasswordBody) => api.patch<unknown>('/auth/me/password', body, { logoutOnAuthError: false }),
}

export interface LoginResult extends DatosSesion {
  token: string
}

/** Guarda token + rol + datos en la sesión y, para EMPRESA, precarga `/empresas/me`. */
export function useAplicarLogin() {
  const { iniciarSesion } = useSession()
  const qc = useQueryClient()
  return ({ token, ...datos }: LoginResult) => {
    // iniciarSesion() vacía la caché: precargar la empresa DESPUÉS.
    iniciarSesion(token, datos)
    if (datos.rol === 'EMPRESA' && datos.empresa?.id_empresa) qc.setQueryData(queryKeys.empresa.me(), datos.empresa)
  }
}

/**
 * Refresca la sesión con `GET /auth/me` (rol, cuenta y `debe_cambiar_password` al día aunque el token sea viejo).
 * Se monta una vez en `RequireAuth`.
 */
export function useSincronizarSesion() {
  const { isAuthenticated, actualizarSesion } = useSession()
  const q = useQuery({ queryKey: ['auth', 'me'], queryFn: authApi.me, enabled: isAuthenticated, staleTime: 60_000 })
  const datos = q.data
  useEffect(() => {
    if (datos) actualizarSesion(datos)
  }, [datos, actualizarSesion])
}

/** OPERARIO / PROVEEDOR: cambia su contraseña y quita la marca `debe_cambiar_password` de la sesión. */
export function useCambiarPasswordCuenta() {
  const qc = useQueryClient()
  const { actualizarSesion } = useSession()
  return useMutation({
    mutationFn: authApi.cambiarPassword,
    onSuccess: () => {
      actualizarSesion({ debeCambiarPassword: false })
      // Las consultas que fallaron con 403 PASSWORD_CHANGE_REQUIRED deben volver a pedirse.
      qc.removeQueries({ predicate: (q) => q.state.status === 'error' })
      void qc.invalidateQueries()
    },
  })
}

/** Inicia sesión y guarda el token en la sesión. */
export function useLogin() {
  const aplicar = useAplicarLogin()
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => aplicar(res),
  })
}

/** El registro queda pendiente hasta abrir el enlace de correo. */
export function useRegister() {
  return useMutation({ mutationFn: authApi.register })
}
