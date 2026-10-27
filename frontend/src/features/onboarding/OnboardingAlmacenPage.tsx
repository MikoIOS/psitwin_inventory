/**
 * Onboarding obligatorio: la empresa debe crear su primer almacén antes de acceder al panel.
 * No hay navegación: la única salida es crear el almacén o cerrar sesión.
 */
import { Navigate, useNavigate } from 'react-router'
import { useCreateAlmacen } from '@/api/almacenes'
import { OnboardingGate, useOnboardingState } from '@/auth/guards'
import { useSession } from '@/auth/SessionContext'
import { useEmpresa } from '@/auth/useEmpresa'
import { Brand } from '@/components/layout/Brand'
import { Button, Card, useToast } from '@/components/ui'
import { AlmacenForm } from '@/features/almacenes/AlmacenForm'
import { paths } from '@/paths'

const PASOS = [
  { n: 1, label: 'Registrar empresa', estado: 'hecho' },
  { n: 2, label: 'Crear primer almacén', estado: 'actual' },
  { n: 3, label: 'Zonas, racks y productos', estado: 'siguiente' },
] as const

function Contenido() {
  const { empresa } = useEmpresa()
  const { cerrarSesion } = useSession()
  const crear = useCreateAlmacen()
  const toast = useToast()
  const navigate = useNavigate()
  const { tieneAlmacenes } = useOnboardingState()

  if (tieneAlmacenes && !crear.isPending && !crear.isSuccess) return <Navigate to={paths.inicio} replace />

  return (
    <div className="min-h-dvh bg-bg">
      <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3 sm:px-8">
        <Brand tone="light" />
        <Button variant="ghost" size="sm" icon="logout" onClick={cerrarSesion}>
          Cerrar sesión
        </Button>
      </header>
      <div className="hazard-stripe h-1" aria-hidden="true" />

      <main className="mx-auto grid w-full max-w-5xl gap-8 px-4 py-8 sm:px-8 lg:grid-cols-[16rem_minmax(0,1fr)] lg:py-12">
        <aside>
          <p className="label-stencil">Configuración inicial</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Bienvenido{empresa?.nombre ? `, ${empresa.nombre}` : ''}
          </h1>
          <p className="mt-2 text-sm text-fg-muted">
            Para empezar a registrar inventario necesitas al menos un almacén. Después podrás dividirlo en zonas y racks.
          </p>
          <ol className="mt-6 flex flex-col gap-3" aria-label="Progreso de configuración">
            {PASOS.map((p) => (
              <li key={p.n} className="flex items-center gap-3 text-sm" aria-current={p.estado === 'actual' ? 'step' : undefined}>
                <span
                  className={
                    p.estado === 'hecho'
                      ? 'flex size-7 items-center justify-center rounded-full bg-success text-xs font-bold text-white'
                      : p.estado === 'actual'
                        ? 'flex size-7 items-center justify-center rounded-full bg-accent font-mono text-xs font-bold text-accent-fg'
                        : 'flex size-7 items-center justify-center rounded-full border border-border-strong font-mono text-xs text-fg-subtle'
                  }
                >
                  {p.estado === 'hecho' ? '✓' : p.n}
                </span>
                <span className={p.estado === 'siguiente' ? 'text-fg-subtle' : 'font-medium text-fg'}>{p.label}</span>
              </li>
            ))}
          </ol>
        </aside>

        <Card eyebrow="Paso 2 de 3" title="Crea tu primer almacén" description="Todos los campos marcados con * son obligatorios.">
          <AlmacenForm
            submitLabel="Crear almacén y continuar"
            onSubmit={(body) => crear.mutateAsync(body)}
            onSuccess={() => {
              toast.success('Almacén creado. ¡Tu panel está listo!')
              navigate(paths.inicio, { replace: true })
            }}
          />
        </Card>
      </main>
    </div>
  )
}

export default function OnboardingAlmacenPage() {
  return (
    <OnboardingGate>
      <Contenido />
    </OnboardingGate>
  )
}
