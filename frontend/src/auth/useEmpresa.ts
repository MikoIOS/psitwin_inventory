import { useEmpresaMe } from '@/api/empresas'
import type { Empresa } from '@/api/types'
import { useSession } from './SessionContext'

export interface UseEmpresaResult {
  empresa: Empresa | undefined
  /** undefined mientras carga. Dentro del layout protegido siempre está definido. */
  id_empresa: string | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

/**
 * Empresa de la sesión. EMPRESA: `GET /empresas/me` (editable en Perfil). OPERARIO / PROVEEDOR: la que devolvió el
 * login (no pueden llamar a `/empresas/me`).
 */
export function useEmpresa(): UseEmpresaResult {
  const { rol, empresa: deSesion } = useSession()
  const q = useEmpresaMe()
  if (rol !== 'EMPRESA') {
    return { empresa: deSesion ?? undefined, id_empresa: deSesion?.id_empresa, isLoading: false, error: null, refetch: () => {} }
  }
  return {
    empresa: q.data,
    id_empresa: q.data?.id_empresa,
    isLoading: q.isPending && q.fetchStatus !== 'idle',
    error: q.error,
    refetch: () => void q.refetch(),
  }
}

/**
 * Id de la empresa para los listados `/x/empresa/{id}` (el backend ya los acota por rol: el OPERARIO recibe solo
 * lo de su almacén). PROVEEDOR → `undefined`: no puede leer esos listados y los hooks quedan deshabilitados.
 */
export function useIdEmpresa(): string | undefined {
  const { rol, empresa } = useSession()
  const q = useEmpresaMe()
  return rol === 'PROVEEDOR' ? undefined : (q.data?.id_empresa ?? empresa?.id_empresa)
}

/** Error lanzado por mutaciones que necesitan id_empresa antes de que cargue. */
export function requireIdEmpresa(id: string | undefined): string {
  if (!id) throw new Error('Los datos de la empresa aún no se han cargado. Inténtalo de nuevo.')
  return id
}
