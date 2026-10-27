/**
 * Empresa autenticada.
 *   GET/PUT/DELETE /empresas/me   PATCH /empresas/me/password
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, apiRequest } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { CambiarPasswordBody, Empresa, EmpresaDeleteBody, EmpresaUpdate } from './types'

export const empresasApi = {
  me: async (): Promise<Empresa> => norm.empresa.one(await api.get('/empresas/me')),
  updateMe: async (body: EmpresaUpdate): Promise<Empresa> => norm.empresa.one(await api.put('/empresas/me', body)),
  cambiarPassword: (body: CambiarPasswordBody) => api.patch<unknown>('/empresas/me/password', body, { logoutOnAuthError: false }),
  /** Exige la contraseña. Contraseña incorrecta → 401: NO debe cerrar la sesión. */
  deleteMe: (body: EmpresaDeleteBody) =>
    apiRequest<unknown>('/empresas/me', { method: 'DELETE', body, logoutOnAuthError: false }),
}

/** Perfil de la empresa autenticada (solo rol EMPRESA). Preferir `useEmpresa()` de `@/auth/useEmpresa`. */
export function useEmpresaMe() {
  const { isAuthenticated, rol } = useSession()
  return useQuery({
    queryKey: queryKeys.empresa.me(),
    queryFn: empresasApi.me,
    enabled: isAuthenticated && rol === 'EMPRESA',
    staleTime: 5 * 60_000,
  })
}

export function useUpdateEmpresa() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: empresasApi.updateMe,
    onSuccess: (empresa) => qc.setQueryData(queryKeys.empresa.me(), empresa),
  })
}

export function useCambiarPassword() {
  return useMutation({ mutationFn: empresasApi.cambiarPassword })
}

/** Elimina la empresa (requiere `{ password }`) y cierra la sesión. */
export function useDeleteEmpresa() {
  const { cerrarSesion } = useSession()
  return useMutation({
    mutationFn: empresasApi.deleteMe,
    onSuccess: () => cerrarSesion(),
  })
}
