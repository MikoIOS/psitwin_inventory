/**
 * Credenciales de las cuentas que crea la EMPRESA (operarios y proveedores):
 *  - `PasswordTemporalInput`: campo de contraseña temporal con «Generar otra» y «Copiar» (formularios de alta).
 *  - `RestablecerPasswordModal`: nueva contraseña temporal (`POST /{operarios|proveedores}/{id}/reset-password`) y la
 *    muestra para entregarla. Si la cuenta no existe aún hace de «Dar acceso» (pide el correo si falta).
 *  - `CredencialesEntregaModal`: muestra correo + contraseña temporal recién creados.
 * El titular deberá cambiar la contraseña al ingresar (`debe_cambiar_password = true`).
 */
import { useState } from 'react'
import type { ResetPasswordBody } from '@/api/types'
import { Badge, Button, Field, Icon, Input, Modal, useApiErrorHandler, useToast } from '@/components/ui'
import { copiarAlPortapapeles, generarPasswordTemporal } from '@/lib/password'

export const MIN_PASSWORD_TEMPORAL = 6

function BloqueCredenciales({ correo, password }: { correo: string | null | undefined; password: string }) {
  const [copiado, setCopiado] = useState(false)
  const texto = `Usuario: ${correo ?? ''}\nContraseña temporal: ${password}`
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid gap-3 rounded-[var(--radius-ui)] border border-border bg-surface-2/60 p-4 text-sm">
        <div>
          <dt className="label-stencil">Usuario (correo)</dt>
          <dd className="mt-0.5 font-mono text-base text-fg" data-testid="credencial-correo">
            {correo ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="label-stencil">Contraseña temporal</dt>
          <dd className="mt-0.5 font-mono text-xl font-semibold tracking-wider text-fg" data-testid="credencial-password">
            {password}
          </dd>
        </div>
      </dl>
      <Button variant="secondary" icon={copiado ? 'check' : 'copy'} className="self-start" onClick={async () => setCopiado(await copiarAlPortapapeles(texto))}>
        {copiado ? 'Copiado' : 'Copiar credenciales'}
      </Button>
      <p className="flex items-start gap-2 text-sm text-fg-muted">
        <Icon name="info" className="mt-0.5 size-4 shrink-0 text-info" />
        Entrégaselas al titular. Por seguridad no se volverán a mostrar; al ingresar deberá cambiar la contraseña.
      </p>
    </div>
  )
}

export function CredencialesEntregaModal({
  datos,
  onClose,
}: {
  datos: { nombre: string; correo: string; password: string } | null
  onClose: () => void
}) {
  return (
    <Modal
      open={!!datos}
      onClose={onClose}
      title="Credenciales de acceso"
      description={datos ? `${datos.nombre} ya puede iniciar sesión.` : undefined}
      footer={<Button onClick={onClose}>Listo</Button>}
    >
      {datos && <BloqueCredenciales correo={datos.correo} password={datos.password} />}
    </Modal>
  )
}

/** Campo controlado de contraseña temporal con «Generar otra» y «Copiar». */
export function PasswordTemporalInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [copiado, setCopiado] = useState(false)
  const set = (v: string) => {
    setCopiado(false)
    onChange(v)
  }
  return (
    <div className="flex flex-col gap-2">
      <Input className="font-mono" autoComplete="off" spellCheck={false} value={value} onChange={(e) => set(e.target.value)} />
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" size="sm" icon="refresh" onClick={() => set(generarPasswordTemporal())}>
          Generar otra
        </Button>
        <Button variant="secondary" size="sm" icon={copiado ? 'check' : 'copy'} onClick={async () => setCopiado(await copiarAlPortapapeles(value))}>
          {copiado ? 'Copiada' : 'Copiar'}
        </Button>
      </div>
    </div>
  )
}

/** Cuenta (operario o proveedor) a la que se le restablece la contraseña / se le da acceso. */
export interface CuentaAcceso {
  id: string
  nombre: string
  correo: string | null | undefined
  tiene_cuenta?: boolean | undefined
}

export interface RestablecerPasswordModalProps {
  cuenta: CuentaAcceso | null
  /** Llama al reset-password del recurso (operario o proveedor). */
  onReset: (id: string, body: ResetPasswordBody) => Promise<unknown>
  onClose: () => void
}

export function RestablecerPasswordModal({ cuenta, onReset, onClose }: RestablecerPasswordModalProps) {
  return (
    <Modal open={!!cuenta} onClose={onClose} title={cuenta && cuenta.tiene_cuenta === false ? 'Dar acceso' : 'Restablecer contraseña'} description={cuenta?.nombre}>
      {cuenta && <Contenido key={cuenta.id} cuenta={cuenta} onReset={onReset} onClose={onClose} />}
    </Modal>
  )
}

function Contenido({ cuenta, onReset, onClose }: { cuenta: CuentaAcceso; onReset: RestablecerPasswordModalProps['onReset']; onClose: () => void }) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const [password, setPassword] = useState(() => generarPasswordTemporal())
  const [correo, setCorreo] = useState('')
  const [estado, setEstado] = useState<'form' | 'enviando' | 'hecho'>('form')
  const pideCorreo = !cuenta.correo
  const correoFinal = cuenta.correo ?? correo.trim().toLowerCase()
  const correoValido = !pideCorreo || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim())
  const valida = password.trim().length >= MIN_PASSWORD_TEMPORAL && correoValido
  const sinCuenta = cuenta.tiene_cuenta === false

  if (estado === 'hecho') {
    return (
      <div className="flex flex-col gap-4">
        <BloqueCredenciales correo={correoFinal} password={password.trim()} />
        <div className="flex justify-end">
          <Button onClick={onClose}>Listo</Button>
        </div>
      </div>
    )
  }

  const enviar = async () => {
    setEstado('enviando')
    try {
      await onReset(cuenta.id, { password_temporal: password.trim(), ...(pideCorreo ? { correo: correoFinal } : {}) })
      setEstado('hecho')
      toast.success('Entrega la contraseña temporal al titular de la cuenta.', sinCuenta ? 'Acceso creado' : 'Contraseña restablecida')
    } catch (e) {
      setEstado('form')
      handleError(e, { title: 'No se pudo restablecer la contraseña' })
    }
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault()
        if (valida) void enviar()
      }}
    >
      <p className="text-sm text-fg-muted">
        {sinCuenta
          ? 'Aún no tiene cuenta: define una contraseña temporal para que pueda iniciar sesión.'
          : 'Se reemplazará la contraseña actual por una temporal. Deberá cambiarla en su próximo ingreso.'}
      </p>
      {pideCorreo && (
        <Field label="Correo de acceso" required error={correo && !correoValido ? 'Correo electrónico no válido' : undefined}>
          <Input type="email" inputMode="email" autoComplete="off" value={correo} onChange={(e) => setCorreo(e.target.value)} placeholder="usuario@empresa.com" />
        </Field>
      )}
      <Field
        label="Contraseña temporal"
        required
        error={password.trim().length >= MIN_PASSWORD_TEMPORAL ? undefined : `Mínimo ${MIN_PASSWORD_TEMPORAL} caracteres`}
      >
        <PasswordTemporalInput value={password} onChange={setPassword} />
      </Field>
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onClose} disabled={estado === 'enviando'}>
          Cancelar
        </Button>
        <Button type="submit" icon="key" loading={estado === 'enviando'} disabled={!valida}>
          {sinCuenta ? 'Dar acceso' : 'Restablecer'}
        </Button>
      </div>
    </form>
  )
}

/** Badges de la cuenta de acceso (operario / proveedor). */
export function BadgesCuenta({ cuenta }: { cuenta: { tiene_cuenta?: boolean | undefined; debe_cambiar_password?: boolean | undefined } }) {
  if (cuenta.tiene_cuenta === false) return <Badge tone="neutral">Sin cuenta</Badge>
  if (cuenta.debe_cambiar_password) return <Badge tone="warning">Debe cambiar contraseña</Badge>
  return null
}
