/**
 * Formulario de cambio de contraseña de OPERARIO / PROVEEDOR (`PATCH /auth/me/password`).
 * Se usa en la pantalla obligatoria de primer ingreso y en «Mi cuenta».
 * Una contraseña actual incorrecta (400/401/403 sin código) se muestra en el campo, sin cerrar la sesión.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { ApiError } from '@/api/client'
import { useCambiarPasswordCuenta } from '@/api/auth'
import { Button, Checkbox, Field, Input, useApiErrorHandler } from '@/components/ui'

const MIN = 6

const schema = z
  .object({
    password_actual: z.string().min(1, 'Ingresa tu contraseña actual'),
    password_nueva: z.string().min(MIN, `Debe tener al menos ${MIN} caracteres`).max(128, 'Máximo 128 caracteres'),
    confirmacion: z.string().min(1, 'Repite la nueva contraseña'),
  })
  .refine((v) => v.password_nueva === v.confirmacion, { message: 'Las contraseñas no coinciden', path: ['confirmacion'] })
  .refine((v) => v.password_nueva !== v.password_actual, { message: 'Debe ser distinta de la actual', path: ['password_nueva'] })
type In = z.input<typeof schema>

export interface CambiarPasswordFormProps {
  /** Texto del campo actual: "Contraseña temporal" en el primer ingreso. */
  etiquetaActual?: string
  submitLabel?: string
  onSuccess?: () => void
  size?: 'md' | 'lg'
}

export function CambiarPasswordForm({ etiquetaActual = 'Contraseña actual', submitLabel = 'Cambiar contraseña', onSuccess, size = 'md' }: CambiarPasswordFormProps) {
  const cambiar = useCambiarPasswordCuenta()
  const handleError = useApiErrorHandler()
  const [ver, setVer] = useState(false)
  const form = useForm<In>({ resolver: zodResolver(schema), defaultValues: { password_actual: '', password_nueva: '', confirmacion: '' } })
  const { register, handleSubmit, formState, reset } = form
  const err = formState.errors
  const tipo = ver ? 'text' : 'password'

  const submit = handleSubmit(async ({ password_actual, password_nueva }) => {
    try {
      await cambiar.mutateAsync({ password_actual, password_nueva })
      reset()
      onSuccess?.()
    } catch (e) {
      if (e instanceof ApiError && (e.status === 400 || e.status === 401 || (e.status === 403 && !e.code)) && !e.hasFieldErrors) {
        form.setError('password_actual', { message: e.status === 403 ? e.detail : 'La contraseña actual no es correcta' }, { shouldFocus: true })
        return
      }
      handleError(e, { form, title: 'No se pudo cambiar la contraseña' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <Field label={etiquetaActual} error={err.password_actual?.message} required>
        <Input type={tipo} size={size} autoComplete="current-password" {...register('password_actual')} />
      </Field>
      <Field label="Nueva contraseña" error={err.password_nueva?.message} required hint={`Mínimo ${MIN} caracteres.`}>
        <Input type={tipo} size={size} autoComplete="new-password" {...register('password_nueva')} />
      </Field>
      <Field label="Repetir nueva contraseña" error={err.confirmacion?.message} required>
        <Input type={tipo} size={size} autoComplete="new-password" {...register('confirmacion')} />
      </Field>
      <Checkbox label="Mostrar contraseñas" checked={ver} onChange={(e) => setVer(e.target.checked)} />
      <Button type="submit" size={size} fullWidth={size === 'lg'} icon="key" loading={cambiar.isPending} className="mt-1 self-start">
        {submitLabel}
      </Button>
    </form>
  )
}
