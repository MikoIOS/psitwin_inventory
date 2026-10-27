import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'
import { useRegister } from '@/api/auth'
import { Button, Field, Input, useApiErrorHandler, useToast } from '@/components/ui'
import { correo, texto } from '@/lib/zod'
import { paths } from '@/paths'
import { AuthLayout } from './AuthLayout'

const schema = z
  .object({
    nombre: texto({ max: 150 }),
    ruc: z.string().trim().regex(/^\d{11}$/, 'El RUC debe tener 11 dígitos'),
    sector: texto({ max: 100 }),
    correo: correo(),
    telefono: z
      .string()
      .trim()
      .regex(/^\+?[\d\s-]{6,20}$/, 'Teléfono no válido (solo dígitos, espacios o guiones)'),
    password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
    confirmar: z.string().min(1, 'Repite la contraseña'),
  })
  .refine((v) => v.password === v.confirmar, { path: ['confirmar'], message: 'Las contraseñas no coinciden' })

type RegistroForm = z.input<typeof schema>

export default function RegistroPage() {
  const registro = useRegister()
  const navigate = useNavigate()
  const toast = useToast()
  const handleError = useApiErrorHandler()

  const form = useForm<RegistroForm>({
    resolver: zodResolver(schema),
    defaultValues: { nombre: '', ruc: '', sector: '', correo: '', telefono: '', password: '', confirmar: '' },
  })
  const { register, handleSubmit, formState } = form
  const err = formState.errors

  const onSubmit = handleSubmit(({ confirmar: _c, ...body }) => {
    registro.mutate(body, {
      onSuccess: ({ token }) => {
        if (token) {
          toast.success('Empresa registrada. Configura tu primer almacén.')
          navigate(paths.onboardingAlmacen, { replace: true })
        } else {
          navigate(`${paths.login}?motivo=registro`, { replace: true })
        }
      },
      onError: (e) => handleError(e, { form, title: 'No se pudo registrar la empresa' }),
    })
  })

  return (
    <AuthLayout
      title="Registrar empresa"
      subtitle="Crea la cuenta de administración de tu empresa."
      footer={
        <>
          ¿Ya tienes cuenta?{' '}
          <Link to={paths.login} className="font-semibold text-fg underline decoration-accent decoration-2 underline-offset-4">
            Inicia sesión
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <Field label="Razón social / nombre" error={err.nombre?.message} required>
          <Input autoComplete="organization" placeholder="PsiTwin Logistics" {...register('nombre')} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="RUC" error={err.ruc?.message} required>
            <Input inputMode="numeric" maxLength={11} placeholder="20123456789" className="font-mono" {...register('ruc')} />
          </Field>
          <Field label="Sector" error={err.sector?.message} required>
            <Input placeholder="Logística" {...register('sector')} />
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Correo" error={err.correo?.message} required hint="Será tu usuario de acceso.">
            <Input type="email" autoComplete="email" inputMode="email" {...register('correo')} />
          </Field>
          <Field label="Teléfono" error={err.telefono?.message} required>
            <Input type="tel" autoComplete="tel" inputMode="tel" placeholder="987654321" {...register('telefono')} />
          </Field>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Contraseña" error={err.password?.message} required hint="Mínimo 6 caracteres.">
            <Input type="password" autoComplete="new-password" {...register('password')} />
          </Field>
          <Field label="Repetir contraseña" error={err.confirmar?.message} required>
            <Input type="password" autoComplete="new-password" {...register('confirmar')} />
          </Field>
        </div>
        <Button type="submit" size="lg" fullWidth loading={registro.isPending} className="mt-2">
          Crear cuenta
        </Button>
      </form>
    </AuthLayout>
  )
}
