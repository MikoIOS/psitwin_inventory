import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'
import { useState } from 'react'
import { authApi } from '@/api/auth'
import { ApiError } from '@/api/client'
import { Button, Field, Input } from '@/components/ui'
import { texto } from '@/lib/zod'
import { paths } from '@/paths'
import { AuthLayout } from './AuthLayout'

export const companySchema = z.object({
  nombre: texto({ min: 2, max: 100 }), nombre_ceo: texto({ max: 100 }),
  ruc: z.string().trim().regex(/^(10|15|16|17|20)\d{9}$/, 'El RUC debe tener 11 dígitos y un prefijo válido').refine(value => {
    if (!/^\d{11}$/.test(value)) return false
    const sum = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2].reduce((total, weight, i) => total + Number(value[i]) * weight, 0)
    return (11 - sum % 11) % 10 === Number(value[10])
  }, 'El dígito de control del RUC no es válido'),
  sector: texto({ min: 2, max: 100 }),
  telefono: z.string().trim().regex(/^\+?[\d\s-]{6,20}$/, 'Teléfono no válido (solo dígitos, espacios o guiones)'),
})
export const registrationSchema = companySchema.extend({
  correo: z.string().trim().toLowerCase().email('Correo no válido').refine(v => v.endsWith('@gmail.com'), 'Utiliza un correo @gmail.com'),
  password: z.string().min(8, 'Usa al menos 8 caracteres').max(128, 'Máximo 128 caracteres'),
  confirmar: z.string().min(1, 'Repite tu contraseña'),
}).refine(v => v.password === v.confirmar, { path: ['confirmar'], message: 'Las contraseñas no coinciden' })

export default function RegistroPage() {
  const [busy, setBusy] = useState(false)
  const [flowError, setFlowError] = useState('')
  const [pendingEmail, setPendingEmail] = useState('')
  const [resendStatus, setResendStatus] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const form = useForm<z.input<typeof registrationSchema>>({ resolver: zodResolver(registrationSchema), mode: 'onChange', defaultValues: { nombre: '', nombre_ceo: '', ruc: '', sector: '', telefono: '', correo: '', password: '', confirmar: '' } })
  const { register, formState: { errors: err }, reset } = form
  const submit = form.handleSubmit(async values => {
    setBusy(true); setFlowError('')
    try {
      await authApi.register({ ...values, password_confirmation: values.confirmar })
      setPendingEmail(values.correo.trim().toLowerCase()); reset()
    } catch (error) {
      setFlowError(error instanceof ApiError ? error.detail : 'No se pudo registrar. Intenta nuevamente.')
    } finally { setBusy(false) }
  })
  async function resend() {
    const correo = pendingEmail || form.getValues('correo')
    if (!correo || !z.email().safeParse(correo).success) { setFlowError('Introduce tu correo para solicitar otro enlace.'); return }
    setBusy(true)
    try { const result = await authApi.resendVerification(correo); setResendStatus(result.message) }
    catch { setFlowError('No se pudo solicitar otro enlace. Intenta más tarde.') }
    finally { setBusy(false) }
  }

  return <AuthLayout title="Registrar empresa" subtitle="Completa los datos de tu empresa para crear tu cuenta PsiTwin."
    footer={<>¿Ya tienes cuenta? <Link to={paths.login} className="font-semibold text-fg underline decoration-accent decoration-2 underline-offset-4">Inicia sesión</Link></>}>
    {flowError && <p role="alert" className="mb-4 text-sm text-danger">{flowError}</p>}
    {pendingEmail && <p role="status" className="mb-5 rounded-md border border-border p-4 text-sm">Revisa tu Gmail {pendingEmail} y abre el enlace para activar tu cuenta. Revisa también Spam. Aún no puedes iniciar sesión.</p>}
    {resendStatus && <p role="status" className="mb-4 text-sm">{resendStatus}</p>}
    {!pendingEmail && <form onSubmit={submit} noValidate className="flex flex-col gap-7">
      <section aria-labelledby="company-heading" className="flex flex-col gap-4">
        <h2 id="company-heading" className="text-sm font-semibold tracking-wide text-accent uppercase">Datos de la empresa</h2>
        <Field label="Nombre de la empresa" required error={err.nombre?.message}><Input autoComplete="organization" placeholder="Nombre de la empresa" {...register('nombre')} /></Field>
        <Field label="Nombre del CEO" required error={err.nombre_ceo?.message}><Input autoComplete="given-name" placeholder="Nombre" maxLength={100} {...register('nombre_ceo')} /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="RUC" required error={err.ruc?.message} hint="11 dígitos. La validación del formato no confirma su existencia."><Input inputMode="numeric" maxLength={11} placeholder="Ingresa el RUC de la empresa" {...register('ruc')} /></Field>
          <Field label="Sector" required error={err.sector?.message}><Input placeholder="Alimentos" {...register('sector')} /></Field>
        </div>
        <Field label="Teléfono" required error={err.telefono?.message}><Input type="tel" autoComplete="tel" placeholder="Ingresa el teléfono" {...register('telefono')} /></Field>
      </section>
      <section aria-labelledby="email-heading" className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 id="email-heading" className="text-sm font-semibold tracking-wide text-accent uppercase">Correo de registro <span className="text-danger">*</span></h2>
        <Field label="Correo Gmail" required error={err.correo?.message}><Input type="email" autoComplete="email" placeholder="usuario@gmail.com" {...register('correo')} /></Field>
      </section>
      <section aria-labelledby="password-heading" className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 id="password-heading" className="text-sm font-semibold tracking-wide text-accent uppercase">Contraseña de PsiTwin</h2>
        <Field label="Contraseña" required error={err.password?.message} hint="Entre 8 y 128 caracteres."><div className="flex gap-2">
          <Input className="min-w-0" type={showPassword ? 'text' : 'password'} autoComplete="new-password" placeholder="Introduce tu contraseña" {...register('password')} />
          <Button type="button" variant="secondary" aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Ocultar' : 'Mostrar'}</Button>
        </div></Field>
        <Field label="Repetir contraseña" required error={err.confirmar?.message}><div className="flex gap-2">
          <Input className="min-w-0" type={showConfirmation ? 'text' : 'password'} autoComplete="new-password" placeholder="Repite tu contraseña" {...register('confirmar')} />
          <Button type="button" variant="secondary" aria-label={showConfirmation ? 'Ocultar repetición de contraseña' : 'Mostrar repetición de contraseña'} aria-pressed={showConfirmation} onClick={() => setShowConfirmation(!showConfirmation)}>{showConfirmation ? 'Ocultar' : 'Mostrar'}</Button>
        </div></Field>
        <p className="text-sm text-fg-muted">Esta contraseña será para ingresar a PsiTwin. No necesitas utilizar tu contraseña de tu cuenta Gmail.</p>
      </section>
      <Button type="submit" size="lg" fullWidth loading={busy}>Registrar empresa</Button>
    </form>}
    <Button type="button" variant="ghost" className="mt-4" loading={busy} onClick={() => void resend()}>Reenviar enlace de verificación</Button>
  </AuthLayout>
}
