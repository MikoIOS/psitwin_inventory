/**
 * Constructores de rutas de la app. Usar siempre estos helpers en <Link to> / navigate()
 * para no duplicar strings (las rutas se registran en `src/routes.tsx`).
 */
const e = encodeURIComponent

export const paths = {
  login: '/login',
  registro: '/registro',
  onboardingAlmacen: '/onboarding/almacen',

  inicio: '/',
  almacen: (idAlmacen: string) => `/almacenes/${e(idAlmacen)}`,
  zona: (idAlmacen: string, idZona: string) => `/almacenes/${e(idAlmacen)}/zonas/${e(idZona)}`,

  productos: '/productos',
  producto: (idProducto: string) => `/productos/${e(idProducto)}`,

  inventario: '/inventario',
  movimientos: '/movimientos',
  operarios: '/operarios',
  proveedores: '/proveedores',

  ordenes: '/ordenes',
  orden: (idOrden: string) => `/ordenes/${e(idOrden)}`,

  recepciones: '/recepciones',
  recepcion: (idRecepcion: string) => `/recepciones/${e(idRecepcion)}`,

  saiki: '/saiki',
  monitoreo: '/monitoreo',
  dispositivo: (id: string) => `/monitoreo/${e(id)}`,
  perfil: '/perfil',
  /** Mi cuenta de operario / proveedor (datos + cambio de contraseña). */
  cuenta: '/cuenta',
  /** Cambio de contraseña obligatorio (contraseña temporal). */
  cambiarPassword: '/cambiar-password',
} as const
