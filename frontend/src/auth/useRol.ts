/**
 * Rol y permisos de la sesión. Las pantallas son las mismas para todos los roles: lo que cambia es qué
 * acciones se muestran. Fuente: docs/ROLES.md (tabla §2 + Desviaciones).
 *
 *   const { rol, esEmpresa, esOperario, esProveedor, idAlmacen, idProveedor } = useRol()
 */
import { useSession } from './SessionContext'

export function useRol() {
  const { rol, operario, proveedor } = useSession()
  return {
    rol,
    esEmpresa: rol === 'EMPRESA',
    esOperario: rol === 'OPERARIO',
    esProveedor: rol === 'PROVEEDOR',
    operario,
    proveedor,
    /** Almacén del operario (el único que ve). */
    idAlmacen: rol === 'OPERARIO' ? (operario?.id_almacen ?? undefined) : undefined,
    idProveedor: rol === 'PROVEEDOR' ? proveedor?.id_proveedor : undefined,
  }
}
