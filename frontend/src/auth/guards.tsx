/**
 * Guards de ruta:
 *  - RequireAuth: exige token (si no, a /login recordando `from`); refresca la sesión con /auth/me; un operario /
 *    proveedor con `debe_cambiar_password` va siempre a /cambiar-password (no puede navegar fuera hasta cambiarla).
 *  - PublicOnly: login/registro; si ya hay sesión, al inicio.
 *  - RequireRol: rutas de ciertos roles; una ruta ajena vuelve al inicio (`/`, que cada rol ve distinto).
 *  - RequireAlmacen: EMPRESA debe tener ≥ 1 almacén (si no, onboarding); OPERARIO debe tener almacén asignado.
 */
import { Navigate, Outlet, useLocation } from 'react-router'
import { useAlmacenes } from '@/api/almacenes'
import { useSincronizarSesion } from '@/api/auth'
import type { Rol } from '@/api/types'
import { Button, EmptyState, ErrorState, LoadingBlock } from '@/components/ui'
import { paths } from '@/paths'
import { useSession } from './SessionContext'
import { useEmpresa } from './useEmpresa'

type Desde = { pathname: string; search?: string } | undefined

/** Destino tras el login: `from` si lo hay (una ruta ajena al rol rebota al inicio); cambio de contraseña primero. */
export function destinoTrasLogin(debeCambiarPassword: boolean, from: Desde): string {
  if (debeCambiarPassword) return paths.cambiarPassword
  const p = from?.pathname
  if (!p || p === paths.login || p === paths.registro || p === paths.cambiarPassword) return paths.inicio
  return `${p}${from.search ?? ''}`
}

export function RequireAuth() {
  const { isAuthenticated, debeCambiarPassword } = useSession()
  const location = useLocation()
  useSincronizarSesion()
  if (!isAuthenticated) return <Navigate to={paths.login} replace state={{ from: location }} />
  if (debeCambiarPassword && location.pathname !== paths.cambiarPassword) return <Navigate to={paths.cambiarPassword} replace />
  return <Outlet />
}

export function PublicOnly() {
  const s = useSession()
  const location = useLocation()
  if (s.isAuthenticated) {
    const from = (location.state as { from?: Desde } | null)?.from
    return <Navigate to={destinoTrasLogin(s.debeCambiarPassword, from)} replace />
  }
  return <Outlet />
}

/** Rutas de ciertos roles. Cualquier otro rol vuelve a su inicio. */
export function RequireRol({ roles }: { roles: Rol[] }) {
  const { rol } = useSession()
  return roles.includes(rol) ? <Outlet /> : <Navigate to={paths.inicio} replace />
}

/** Pantalla completa de carga/error mientras se resuelve la empresa y sus almacenes. */
function FullScreen({ children }: { children: React.ReactNode }) {
  return <div className="flex min-h-dvh items-center justify-center bg-bg p-6">{children}</div>
}

/** Estado de onboarding: carga empresa + almacenes. Reutilizado por RequireAlmacen y la página de onboarding. */
export function useOnboardingState() {
  const empresa = useEmpresa()
  const almacenes = useAlmacenes()
  const isLoading = empresa.isLoading || (!!empresa.id_empresa && almacenes.isPending)
  const error = empresa.error ?? almacenes.error
  return {
    isLoading,
    error,
    retry: () => {
      empresa.refetch()
      void almacenes.refetch()
    },
    tieneAlmacenes: (almacenes.data?.length ?? 0) > 0,
  }
}

export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const { cerrarSesion } = useSession()
  const st = useOnboardingState()
  if (st.isLoading)
    return (
      <FullScreen>
        <LoadingBlock label="Preparando tu panel…" />
      </FullScreen>
    )
  if (st.error)
    return (
      <FullScreen>
        <div className="flex w-full max-w-md flex-col items-center gap-4">
          <ErrorState error={st.error} onRetry={st.retry} className="w-full" />
          <Button variant="ghost" icon="logout" onClick={cerrarSesion}>
            Cerrar sesión
          </Button>
        </div>
      </FullScreen>
    )
  return <>{children}</>
}

export function RequireAlmacen() {
  const { rol, operario, cerrarSesion } = useSession()
  if (rol === 'PROVEEDOR') return <Outlet />
  if (rol === 'OPERARIO') {
    if (operario?.id_almacen) return <Outlet />
    return (
      <FullScreen>
        <EmptyState
          icon="warehouse"
          title="Sin almacén asignado"
          description="Tu cuenta aún no tiene un almacén. Pide a tu empresa que te asigne uno."
          action={
            <Button variant="secondary" icon="logout" onClick={cerrarSesion}>
              Cerrar sesión
            </Button>
          }
        />
      </FullScreen>
    )
  }
  return <RequireAlmacenEmpresa />
}

function RequireAlmacenEmpresa() {
  const st = useOnboardingState()
  const location = useLocation()
  return (
    <OnboardingGate>
      {!st.isLoading && !st.error && !st.tieneAlmacenes && !['/', '/perfil', '/saiki'].includes(location.pathname) ? <Navigate to={paths.onboardingAlmacen} replace /> : <Outlet />}
    </OnboardingGate>
  )
}
