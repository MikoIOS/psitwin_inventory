/**
 * Perfil de la empresa autenticada:
 *  - Editar datos generales (PUT /empresas/me), incluido el RUC (8–20 caracteres).
 *  - Cambiar contraseña (PATCH /empresas/me/password) pidiendo la actual + nueva + confirmación.
 *  - Eliminar la empresa (DELETE /empresas/me, body `{ password }`) con confirmación fuerte
 *    (escribir el nombre + contraseña) → cierra sesión.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useId, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCambiarPassword, useDeleteEmpresa, useUpdateEmpresa } from '@/api/empresas'
import { ApiError } from '@/api/client'
import type { Empresa, EmpresaUpdate } from '@/api/types'
import { useEmpresa } from '@/auth/useEmpresa'
import { Button, Card, ErrorState, Field, Icon, Input, LoadingBlock, Modal, PageHeader, useApiErrorHandler, useToast } from '@/components/ui'
import { formatFecha } from '@/lib/format'
import { correo, texto } from '@/lib/zod'

export default function PerfilPage() {
  const { empresa, isLoading, error, refetch } = useEmpresa()

  return (
    <>
      <PageHeader eyebrow="Cuenta" title="Perfil de la empresa" description="Datos de la organización, acceso y opciones de la cuenta." />
      {isLoading ? (
        <LoadingBlock label="Cargando perfil…" />
      ) : error || !empresa ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <DatosEmpresaCard key={empresa.id_empresa} empresa={empresa} />
          <PasswordCard />
          <WelcomeEmailCard />
          <ZonaPeligro empresa={empresa} />
        </div>
      )}
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Datos de la empresa                                                  */
/* ------------------------------------------------------------------ */

const empresaSchema = z.object({
  nombre: texto({ min: 2, max: 100 }),
  nombre_ceo: z.string().trim().max(100).optional(),
  ruc: texto({ min: 8, max: 20 }).regex(/^[0-9]+$/, 'Solo dígitos'),
  sector: texto({ min: 2, max: 100 }),
  correo: correo(),
  telefono: texto({ min: 6, max: 20 }).regex(/^[0-9+()\s-]+$/, 'Solo números, espacios y + ( ) -'),
})
type EmpresaIn = z.input<typeof empresaSchema>
type EmpresaOut = z.output<typeof empresaSchema>
const _checkEmpresa: (v: EmpresaOut) => EmpresaUpdate = (v) => v
void _checkEmpresa

const empresaDefaults = (e: Empresa): EmpresaIn => ({ nombre: e.nombre, nombre_ceo: e.nombre_ceo ?? '', ruc: e.ruc, sector: e.sector, correo: e.correo, telefono: e.telefono })

function DatosEmpresaCard({ empresa }: { empresa: Empresa }) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const actualizar = useUpdateEmpresa()
  const form = useForm<EmpresaIn, unknown, EmpresaOut>({ resolver: zodResolver(empresaSchema), defaultValues: empresaDefaults(empresa) })
  const { register, handleSubmit, formState, reset } = form
  const err = formState.errors

  const submit = handleSubmit(async (body) => {
    try {
      const { nombre_ceo, ...other } = body
      const actualizada = await actualizar.mutateAsync({ ...other, ...(nombre_ceo ? { nombre_ceo } : {}) })
      reset(empresaDefaults(actualizada))
      toast.success('Datos de la empresa actualizados')
    } catch (e) {
      handleError(e, { form, title: 'No se pudieron guardar los datos' })
    }
  })

  return (
    <Card eyebrow="Empresa" title="Datos generales" description="Se muestran en los documentos y órdenes de reposición.">
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-4 rounded-[var(--radius-ui)] border border-border bg-surface-2/50 p-3 text-sm">
          <div>
            <dt className="text-xs text-fg-subtle">Registrada</dt>
            <dd className="font-medium">{formatFecha(empresa.fecha_creacion)}</dd>
          </div>
          <div>
            <dt className="text-xs text-fg-subtle">Última actualización</dt>
            <dd className="font-medium">{formatFecha(empresa.fecha_actualizacion)}</dd>
          </div>
        </dl>
        <div className="grid gap-4 sm:grid-cols-[1fr_12rem]">
          <Field label="Nombre de la empresa" error={err.nombre?.message} required>
            <Input autoComplete="organization" {...register('nombre')} />
          </Field>
          <Field label="RUC" error={err.ruc?.message} required>
            <Input inputMode="numeric" className="font-mono" maxLength={20} {...register('ruc')} />
          </Field>
        </div>
        <Field label="Nombre del CEO" error={err.nombre_ceo?.message}>
          <Input placeholder="Nombre" autoComplete="given-name" {...register('nombre_ceo')} />
        </Field>
        <Field label="Sector" error={err.sector?.message} required>
          <Input placeholder="Alimentos" {...register('sector')} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Correo" error={err.correo?.message} required hint="Se usa para iniciar sesión.">
            <Input type="email" autoComplete="email" inputMode="email" {...register('correo')} />
          </Field>
          <Field label="Teléfono" error={err.telefono?.message} required>
            <Input type="tel" autoComplete="tel" inputMode="tel" {...register('telefono')} />
          </Field>
        </div>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={() => reset(empresaDefaults(empresa))} disabled={!formState.isDirty || formState.isSubmitting}>
            Descartar
          </Button>
          <Button type="submit" icon="check" loading={formState.isSubmitting} disabled={!formState.isDirty}>
            Guardar cambios
          </Button>
        </div>
      </form>
    </Card>
  )
}

function WelcomeEmailCard() {
  const { empresa } = useEmpresa()
  const status = useQuery({ queryKey: ['empresa', 'bienvenida', empresa?.id_empresa], queryFn: () => api.get<{ status: string; intentos: number }>('/empresas/me/bienvenida'), refetchInterval: query => ['PENDIENTE', 'ENVIANDO'].includes(query.state.data?.status ?? '') ? 3000 : false })
  const resend = useMutation({ mutationFn: () => api.post('/empresas/me/bienvenida/reintentar', {}), onSuccess: () => void status.refetch() })
  const labels: Record<string, string> = { ENVIADO: 'Correo enviado', PENDIENTE: 'Pendiente de envío', CONFIRMACION_PENDIENTE: 'Verifica tu correo para recibir la bienvenida', CONFIGURACION_PENDIENTE: 'Pendiente de configurar el correo', ERROR: 'No se pudo enviar', ENVIANDO: 'Enviando o pendiente de confirmar', REVISAR_ENVIO: 'Es necesario revisar el resultado del envío', NO_SOLICITADO: 'Sin correo de bienvenida solicitado' }
  return <Card title="Correo de bienvenida"><p className="mb-3 text-sm text-fg-muted">{status.isError ? 'No se pudo consultar el estado.' : labels[status.data?.status ?? ''] ?? 'Consultando…'}</p>
    <Button variant="secondary" loading={resend.isPending} disabled={!empresa?.nombre_ceo || !empresa?.correo_verificado || ['ENVIADO', 'ENVIANDO', 'REVISAR_ENVIO'].includes(status.data?.status ?? '')} onClick={() => resend.mutate()}>Reintentar bienvenida</Button>
    {!empresa?.correo_verificado && <p className="mt-2 text-xs text-fg-muted">Verifica tu correo para recibir la bienvenida.</p>}
    {!empresa?.nombre_ceo && <p className="mt-2 text-xs text-fg-muted">Guarda el nombre del CEO para personalizar la bienvenida.</p>}
    {resend.isError && <p role="alert" className="mt-3 text-sm text-danger">{resend.error instanceof ApiError ? resend.error.detail : 'No se pudo solicitar el envío.'}</p>}
  </Card>
}

/* ------------------------------------------------------------------ */
/* Contraseña                                                           */
/* ------------------------------------------------------------------ */

const MIN_PASSWORD = 6

const passwordSchema = z
  .object({
    password_actual: z.string().min(1, 'Ingresa tu contraseña actual'),
    password_nueva: z.string().min(MIN_PASSWORD, `Debe tener al menos ${MIN_PASSWORD} caracteres`).max(128, 'Máximo 128 caracteres'),
    confirmacion: z.string().min(1, 'Repite la nueva contraseña'),
  })
  .refine((v) => v.password_nueva === v.confirmacion, { message: 'Las contraseñas no coinciden', path: ['confirmacion'] })
  .refine((v) => v.password_nueva !== v.password_actual, { message: 'La nueva contraseña debe ser distinta de la actual', path: ['password_nueva'] })
type PasswordIn = z.input<typeof passwordSchema>
type PasswordOut = z.output<typeof passwordSchema>

function PasswordCard() {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const cambiar = useCambiarPassword()
  const [ver, setVer] = useState(false)
  const form = useForm<PasswordIn, unknown, PasswordOut>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { password_actual: '', password_nueva: '', confirmacion: '' },
  })
  const { register, handleSubmit, formState, reset } = form
  const err = formState.errors
  const tipo = ver ? 'text' : 'password'

  const submit = handleSubmit(async ({ password_actual, password_nueva }) => {
    try {
      await cambiar.mutateAsync({ password_actual, password_nueva })
      reset()
      setVer(false)
      toast.success('Contraseña actualizada')
    } catch (e) {
      if (e instanceof ApiError && [400, 401, 403].includes(e.status)) {
        form.setError('password_actual', { message: 'La contraseña actual no es correcta' })
        return
      }
      handleError(e, { form, title: 'No se pudo cambiar la contraseña' })
    }
  })

  return (
    <Card eyebrow="Seguridad" title="Cambiar contraseña" description="Por seguridad, confirma tu contraseña actual." className="self-start">
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <Field label="Contraseña actual" error={err.password_actual?.message} required>
          <Input type={tipo} autoComplete="current-password" {...register('password_actual')} />
        </Field>
        <Field label="Nueva contraseña" error={err.password_nueva?.message} required hint={`Mínimo ${MIN_PASSWORD} caracteres.`}>
          <Input type={tipo} autoComplete="new-password" {...register('password_nueva')} />
        </Field>
        <Field label="Confirmar nueva contraseña" error={err.confirmacion?.message} required>
          <Input type={tipo} autoComplete="new-password" {...register('confirmacion')} />
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
          <Button variant="ghost" size="sm" onClick={() => setVer((v) => !v)} aria-pressed={ver}>
            {ver ? 'Ocultar contraseñas' : 'Mostrar contraseñas'}
          </Button>
          <Button type="submit" loading={formState.isSubmitting}>
            Cambiar contraseña
          </Button>
        </div>
      </form>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/* Eliminar empresa                                                     */
/* ------------------------------------------------------------------ */

function ZonaPeligro({ empresa }: { empresa: Empresa }) {
  const [abierto, setAbierto] = useState(false)
  return (
    <Card accent="danger" eyebrow="Zona de peligro" title="Eliminar empresa" className="lg:col-span-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-2xl text-sm text-fg-muted">
          Elimina la cuenta de <strong className="text-fg">{empresa.nombre}</strong> y cierra la sesión. Esta acción es permanente y no se puede
          deshacer.
        </p>
        <Button variant="danger" icon="trash" onClick={() => setAbierto(true)}>
          Eliminar empresa
        </Button>
      </div>
      {abierto && <EliminarEmpresaModal empresa={empresa} onClose={() => setAbierto(false)} />}
    </Card>
  )
}

function EliminarEmpresaModal({ empresa, onClose }: { empresa: Empresa; onClose: () => void }) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const eliminar = useDeleteEmpresa()
  const [confirmTexto, setConfirmTexto] = useState('')
  const [password, setPassword] = useState('')
  const [errorPassword, setErrorPassword] = useState<string | null>(null)
  const inputId = useId()
  const passwordId = useId()
  const coincide = confirmTexto.trim() === empresa.nombre.trim()
  const puedeEnviar = coincide && password.length >= MIN_PASSWORD

  const confirmar = async () => {
    if (!puedeEnviar) return
    setErrorPassword(null)
    try {
      // Al terminar, useDeleteEmpresa cierra la sesión y el guard redirige a /login.
      await eliminar.mutateAsync({ password })
      toast.success('La empresa fue eliminada. Sesión cerrada.')
    } catch (e) {
      // Contraseña incorrecta → 401 (el cliente NO cierra la sesión en esta llamada).
      if (e instanceof ApiError && (e.status === 401 || e.status === 403 || e.status === 400)) {
        setErrorPassword('La contraseña no es correcta')
        return
      }
      handleError(e, { title: 'No se pudo eliminar la empresa' })
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      dismissable={!eliminar.isPending}
      size="sm"
      title="Eliminar empresa"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={eliminar.isPending}>
            Cancelar
          </Button>
          <Button variant="danger" type="submit" form={`${inputId}-form`} loading={eliminar.isPending} disabled={!puedeEnviar}>
            Eliminar definitivamente
          </Button>
        </>
      }
    >
      <form
        id={`${inputId}-form`}
        noValidate
        onSubmit={(e) => {
          e.preventDefault()
          void confirmar()
        }}
        className="flex flex-col gap-4"
      >
        <div className="flex gap-3 rounded-[var(--radius-ui)] border border-danger/30 bg-danger-soft px-3 py-2.5 text-sm text-danger">
          <Icon name="alert" className="mt-0.5 size-4 shrink-0" />
          <p>Se eliminarán la cuenta y el acceso de la empresa. Si existen datos asociados, el sistema puede impedirlo.</p>
        </div>
        <Field
          id={inputId}
          label={
            <>
              Escribe <strong className="font-mono">{empresa.nombre}</strong> para confirmar
            </>
          }
        >
          <Input value={confirmTexto} onChange={(e) => setConfirmTexto(e.target.value)} autoComplete="off" spellCheck={false} autoFocus />
        </Field>
        <Field id={passwordId} label="Contraseña de la cuenta" required error={errorPassword ?? undefined} hint="Por seguridad, confirma con tu contraseña.">
          <Input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              setErrorPassword(null)
            }}
          />
        </Field>
      </form>
    </Modal>
  )
}
