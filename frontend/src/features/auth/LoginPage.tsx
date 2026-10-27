import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate, useSearchParams, type Location } from 'react-router'
import { z } from 'zod'
import { useLogin } from '@/api/auth'
import { destinoTrasLogin } from '@/auth/guards'
import { ApiError } from '@/api/client'
import { Button, Field, Icon, Input, useApiErrorHandler } from '@/components/ui'
import { correo } from '@/lib/zod'
import { paths } from '@/paths'
import { AuthLayout } from './AuthLayout'

const schema = z.object({
  correo: correo(),
  password: z.string().min(1, 'Ingresa tu contraseña'),
})
type LoginForm = z.input<typeof schema>

const AVISOS: Record<string, { tone: 'warning' | 'danger' | 'info'; text: string }> = {
  expirada: { tone: 'warning', text: 'Tu sesión expiró. Inicia sesión nuevamente.' },
  prohibido: { tone: 'danger', text: 'Acceso no permitido. Inicia sesión con una cuenta autorizada.' },
  inactivo: { tone: 'danger', text: 'Tu cuenta fue desactivada. Consulta con tu empresa.' },
  registro: { tone: 'info', text: 'Tu empresa fue registrada. Inicia sesión para continuar.' },
}

const AVISO_CLASS = {
  warning: 'border-warning/30 bg-warning-soft text-warning',
  danger: 'border-danger/30 bg-danger-soft text-danger',
  info: 'border-info/30 bg-info-soft text-info',
}

export default function LoginPage() {
  const login = useLogin()
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const handleError = useApiErrorHandler()
  const [credencialesInvalidas, setCredencialesInvalidas] = useState(false)
  const [accesoDenegado, setAccesoDenegado] = useState<string | null>(null)

  const form = useForm<LoginForm>({ resolver: zodResolver(schema), defaultValues: { correo: '', password: '' } })
  const { register, handleSubmit, formState } = form

  const aviso = AVISOS[params.get('motivo') ?? '']
  const from = (location.state as { from?: Location } | null)?.from

  const onSubmit = handleSubmit((values) => {
    setCredencialesInvalidas(false)
    setAccesoDenegado(null)
    login.mutate(values, {
      // Un único login para los tres roles: cada uno ve su propio inicio en `/`.
      onSuccess: (r) => navigate(destinoTrasLogin(r.debeCambiarPassword, from), { replace: true }),
      onError: (err) => {
        if (err instanceof ApiError && (err.status === 401 || err.status === 400 || err.status === 404)) {
          setCredencialesInvalidas(true)
          return
        }
        if (err instanceof ApiError && err.status === 403) {
          // p. ej. "Operario inactivo" / "Proveedor inactivo"
          setAccesoDenegado(err.detail)
          return
        }
        handleError(err, { form, title: 'No se pudo iniciar sesión' })
      },
    })
  })

  return (
    <AuthLayout
      title="Iniciar sesión"
      subtitle="Empresa, operario o proveedor: un solo acceso."
      footer={
        <div className="flex flex-col gap-2">
          <p>
            ¿Tu empresa aún no tiene cuenta?{' '}
            <Link to={paths.registro} className="font-semibold text-fg underline decoration-accent decoration-2 underline-offset-4">
              Regístrala aquí
            </Link>
          </p>
          <p className="flex items-start gap-1.5">
            <Icon name="user" className="mt-0.5 size-4 shrink-0" />
            ¿Eres operario o proveedor? Pide tus credenciales a la empresa.
          </p>
        </div>
      }
    >
      {aviso && (
        <p role="status" className={`mb-5 flex items-start gap-2 rounded-md border px-3 py-2.5 text-sm ${AVISO_CLASS[aviso.tone]}`}>
          <Icon name={aviso.tone === 'info' ? 'info' : 'alert'} className="mt-0.5 size-4 shrink-0" />
          {aviso.text}
        </p>
      )}

      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <Field label="Correo" error={formState.errors.correo?.message} required>
          <Input type="email" autoComplete="email" inputMode="email" size="lg" placeholder="usuario@empresa.com" {...register('correo')} />
        </Field>
        <Field label="Contraseña" error={formState.errors.password?.message} required>
          <Input type="password" autoComplete="current-password" size="lg" {...register('password')} />
        </Field>

        {credencialesInvalidas && (
          <p role="alert" className="flex items-center gap-2 rounded-md border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger">
            <Icon name="alert" className="size-4 shrink-0" />
            Correo o contraseña incorrectos.
          </p>
        )}
        {accesoDenegado && (
          <p role="alert" className="flex items-center gap-2 rounded-md border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger">
            <Icon name="alert" className="size-4 shrink-0" />
            {accesoDenegado}
          </p>
        )}

        <Button type="submit" size="lg" fullWidth loading={login.isPending} className="mt-2">
          Ingresar
        </Button>
      </form>
    </AuthLayout>
  )
}
