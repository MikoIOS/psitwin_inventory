/**
 * Cambio de contraseña OBLIGATORIO de operario / proveedor (primer ingreso o tras un restablecimiento).
 * Mientras `debe_cambiar_password` sea true, `RequireAuth` devuelve aquí cualquier otra ruta. Si no aplica → al inicio.
 */
import { Navigate, useNavigate } from 'react-router'
import { useSession } from '@/auth/SessionContext'
import { Icon, useToast } from '@/components/ui'
import { AuthLayout } from '@/features/auth/AuthLayout'
import { paths } from '@/paths'
import { CambiarPasswordForm } from './CambiarPasswordForm'

export default function CambiarPasswordPage() {
  const s = useSession()
  const navigate = useNavigate()
  const toast = useToast()

  if (!s.debeCambiarPassword) return <Navigate to={paths.inicio} replace />
  const nombre = s.operario?.nombre ?? s.proveedor?.nombre

  return (
    <AuthLayout
      title="Crea tu contraseña"
      subtitle={
        <>
          {nombre ? `Hola, ${nombre}. ` : ''}Estás usando una contraseña temporal entregada por tu empresa. Para continuar, define una
          contraseña personal.
        </>
      }
      footer={
        <button type="button" onClick={s.cerrarSesion} className="inline-flex items-center gap-1.5 font-medium text-fg-muted hover:text-fg">
          <Icon name="logout" className="size-4" />
          Cerrar sesión
        </button>
      }
    >
      <p role="status" className="mb-5 flex items-start gap-2 rounded-md border border-warning/30 bg-warning-soft px-3 py-2.5 text-sm text-warning">
        <Icon name="key" className="mt-0.5 size-4 shrink-0" />
        No podrás usar el sistema hasta cambiarla.
      </p>
      <CambiarPasswordForm
        etiquetaActual="Contraseña temporal"
        submitLabel="Guardar y continuar"
        size="lg"
        onSuccess={() => {
          toast.success('Ya puedes usar el sistema con tu nueva contraseña.', 'Contraseña actualizada')
          navigate(paths.inicio, { replace: true })
        }}
      />
    </AuthLayout>
  )
}
