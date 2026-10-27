import { isRouteErrorResponse, useRouteError } from 'react-router'
import { EmptyState, ErrorState, LinkButton } from '@/components/ui'
import { paths } from '@/paths'

/** errorElement de las rutas: 404 de router, fallos de carga lazy y errores de render. */
export function RouteError() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundContent />
  console.error(error)
  return (
    <div className="py-10">
      <ErrorState
        title="Algo salió mal al mostrar esta página"
        error={error instanceof Error ? error : new Error('Error inesperado')}
        onRetry={() => window.location.reload()}
      />
    </div>
  )
}

function NotFoundContent() {
  return (
    <div className="py-10">
      <EmptyState
        icon="search"
        title="Página no encontrada"
        description="La dirección no existe o fue movida."
        action={
          <LinkButton to={paths.inicio} icon="arrow-left">
            Volver al inicio
          </LinkButton>
        }
      />
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-bg p-6">
      <div className="w-full max-w-md">
        <NotFoundContent />
      </div>
    </div>
  )
}
