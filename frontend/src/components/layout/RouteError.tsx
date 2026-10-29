import { isRouteErrorResponse, useRouteError } from 'react-router'
import { EmptyState, ErrorState, LinkButton } from '@/components/ui'
import { paths } from '@/paths'
import { isChunkLoadError } from '@/lib/chunkRecovery'

/** errorElement de las rutas: 404 de router, fallos de carga lazy y errores de render. */
export function RouteError() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundContent />
  console.error(error)
  const chunkError = isChunkLoadError(error)
  return (
    <div className="py-10">
      <ErrorState
        title={chunkError ? 'No se pudo cargar esta sección' : 'Algo salió mal al mostrar esta página'}
        error={chunkError
          ? new Error('La aplicación pudo actualizarse o la conexión se interrumpió. Recarga la página para volver a intentarlo.')
          : error instanceof Error ? error : new Error('Error inesperado')}
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
