import type { IconName } from '@/components/ui/Icon'
import type { Rol } from '@/api/types'
import { paths } from '@/paths'

export interface NavItem {
  to: string
  label: string
  icon: IconName
  /** Solo activo en coincidencia exacta (para "/"). */
  end?: boolean
  /** Grupo visual en el sidebar. */
  grupo: 'operacion' | 'reposicion' | 'cuenta'
  /** Roles que ven el ítem (y pueden entrar a la ruta: ver `routes.tsx`). */
  roles: Rol[]
}

export const NAV_GRUPOS: Record<NavItem['grupo'], string> = {
  operacion: 'Operación',
  reposicion: 'Reposición',
  cuenta: 'Cuenta',
}

const E: Rol = 'EMPRESA'
const O: Rol = 'OPERARIO'
const P: Rol = 'PROVEEDOR'

export const NAV_ITEMS: NavItem[] = [
  { to: paths.inicio, label: 'Inicio', icon: 'warehouse', end: true, grupo: 'operacion', roles: [E, O, P] },
  { to: paths.productos, label: 'Productos', icon: 'box', grupo: 'operacion', roles: [E, O, P] },
  { to: paths.inventario, label: 'Inventario', icon: 'layers', grupo: 'operacion', roles: [E, O] },
  { to: paths.movimientos, label: 'Movimientos', icon: 'arrows', grupo: 'operacion', roles: [E, O] },
  { to: paths.monitoreo, label: 'Monitoreo', icon: 'snowflake', grupo: 'operacion', roles: [E, O] },
  { to: paths.saiki, label: 'Saiki (asistente)', icon: 'info', grupo: 'operacion', roles: [E] },
  { to: paths.operarios, label: 'Operarios', icon: 'users', grupo: 'operacion', roles: [E] },
  { to: paths.proveedores, label: 'Proveedores', icon: 'truck', grupo: 'reposicion', roles: [E] },
  { to: paths.ordenes, label: 'Solicitudes de reposición', icon: 'clipboard', grupo: 'reposicion', roles: [E, O] },
  { to: paths.recepciones, label: 'Recepciones', icon: 'inbox', grupo: 'reposicion', roles: [E, O] },
  { to: paths.perfil, label: 'Perfil', icon: 'building', grupo: 'cuenta', roles: [E] },
  { to: paths.cuenta, label: 'Mi cuenta', icon: 'user', grupo: 'cuenta', roles: [O, P] },
]
