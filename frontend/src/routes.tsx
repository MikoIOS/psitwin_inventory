/**
 * Registro de rutas. Las páginas de módulos se cargan en diferido (code splitting por módulo).
 * Para rutas nuevas: añadir el path en `src/paths.ts` y registrarlo aquí con `page(() => import(...))`.
 * Cada página debe tener `export default`.
 *
 * Las rutas son las mismas para los tres roles; `RequireRol` decide quién entra (una ruta ajena vuelve a `/`) y
 * cada página muestra las acciones que su rol permite (`useRol()`). Debe coincidir con `roles` de `navigation.ts`.
 */
import type { ComponentType } from 'react'
import { createBrowserRouter, type RouteObject } from 'react-router'
import { PublicOnly, RequireAlmacen, RequireAuth, RequireRol } from '@/auth/guards'
import { AppLayout } from '@/components/layout/AppLayout'
import { NotFoundPage, RouteError } from '@/components/layout/RouteError'
import LoginPage from '@/features/auth/LoginPage'
import RegistroPage from '@/features/auth/RegistroPage'
import VerifyEmailPage from '@/features/auth/VerifyEmailPage'
import CambiarPasswordPage from '@/features/cuenta/CambiarPasswordPage'
import InicioPorRol from '@/features/inicio/InicioPorRol'
import OnboardingAlmacenPage from '@/features/onboarding/OnboardingAlmacenPage'

/** Ruta lazy: `page(() => import('./features/x/XPage'))`. */
function page(load: () => Promise<{ default: ComponentType }>): Pick<RouteObject, 'lazy'> {
  return { lazy: async () => ({ Component: (await load()).default }) }
}

export const routes: RouteObject[] = [
  {
    errorElement: <RouteError />,
    children: [
      { path: '/verificar-correo', element: <VerifyEmailPage /> },
      {
        element: <PublicOnly />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/registro', element: <RegistroPage /> },
        ],
      },
      {
        element: <RequireAuth />,
        children: [
          { path: '/cambiar-password', element: <CambiarPasswordPage /> },
          { element: <RequireRol roles={['EMPRESA']} />, children: [{ path: '/onboarding/almacen', element: <OnboardingAlmacenPage /> }] },
          {
            element: <RequireAlmacen />,
            children: [
              {
                element: <AppLayout />,
                children: [
                  {
                    // Ruta sin path: captura errores de las páginas sin perder el layout.
                    errorElement: <RouteError />,
                    children: [
                      { index: true, element: <InicioPorRol /> },
                      { path: 'productos', ...page(() => import('@/features/productos/ProductosPage')) },
                      { path: 'abastecimiento', ...page(() => import('@/features/abastecimiento/AbastecimientoPage')) },
                      { path: 'productos/:idProducto', ...page(() => import('@/features/productos/ProductoDetallePage')) },
                      { path: 'ordenes/:idOrden', ...page(() => import('@/features/ordenes/OrdenDetallePage')) },
                      {
                        element: <RequireRol roles={['EMPRESA', 'OPERARIO']} />,
                        children: [
                          { path: 'analisis', ...page(() => import('@/features/analisis/AnalisisPage')) },
                          { path: 'saiki', ...page(() => import('@/features/saiki/SaikiPage')) },
                          { path: 'almacenes/:idAlmacen/plano', ...page(() => import('@/features/almacenes/PlanoAlmacenPage')) },
                          { path: 'almacenes/:idAlmacen', ...page(() => import('@/features/almacenes/AlmacenDetallePage')) },
                          { path: 'almacenes/:idAlmacen/zonas/:idZona', ...page(() => import('@/features/almacenes/ZonaDetallePage')) },
                          { path: 'inventario', ...page(() => import('@/features/inventario/InventarioPage')) },
                          { path: 'monitoreo', ...page(() => import('@/features/monitoreo/MonitoreoPage')) },
                          { path: 'monitoreo/:idDispositivo', ...page(() => import('@/features/monitoreo/DispositivoDetallePage')) },
                          { path: 'movimientos', ...page(() => import('@/features/movimientos/MovimientosPage')) },
                          { path: 'ordenes', ...page(() => import('@/features/ordenes/OrdenesPage')) },
                          { path: 'recepciones', ...page(() => import('@/features/recepciones/RecepcionesPage')) },
                          { path: 'recepciones/:idRecepcion', ...page(() => import('@/features/recepciones/RecepcionDetallePage')) },
                        ],
                      },
                      {
                        element: <RequireRol roles={['EMPRESA']} />,
                        children: [
                          { path: 'operarios', ...page(() => import('@/features/operarios/OperariosPage')) },
                          { path: 'proveedores', ...page(() => import('@/features/proveedores/ProveedoresPage')) },
                          { path: 'perfil', ...page(() => import('@/features/perfil/PerfilPage')) },
                        ],
                      },
                      {
                        element: <RequireRol roles={['OPERARIO', 'PROVEEDOR']} />,
                        children: [{ path: 'cuenta', ...page(() => import('@/features/cuenta/MiCuentaPage')) }],
                      },
                    ],
                  },
                ],
              },
            ],
          },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]

export const router = createBrowserRouter(routes)
