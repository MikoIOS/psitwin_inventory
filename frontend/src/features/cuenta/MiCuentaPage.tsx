/** Mi cuenta (OPERARIO / PROVEEDOR): sus datos (solo lectura; los administra la empresa) y cambio de contraseña. */
import type { ReactNode } from 'react'
import { useAlmacen } from '@/api/almacenes'
import { etiquetaTurno } from '@/api/enums'
import { useEmpresa } from '@/auth/useEmpresa'
import { useRol } from '@/auth/useRol'
import { Card, PageHeader, StatusBadge, useToast } from '@/components/ui'
import { textoOVacio } from '@/lib/format'
import { CambiarPasswordForm } from './CambiarPasswordForm'

export default function MiCuentaPage() {
  const toast = useToast()
  const { operario, proveedor, idAlmacen } = useRol()
  const { empresa } = useEmpresa()
  const almacen = useAlmacen(idAlmacen).data

  return (
    <>
      <PageHeader eyebrow="Cuenta" title="Mi cuenta" description="Tus datos los administra la empresa. Aquí puedes cambiar tu contraseña." />
      <div className="grid gap-5 lg:grid-cols-2">
        <Card padding="md" title="Mis datos">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            {operario && (
              <>
                <Dato label="Nombre">
                  {operario.nombre} {operario.apellido}
                </Dato>
                <Dato label="Estado">
                  <StatusBadge estado={operario.estado} />
                </Dato>
                <Dato label="Correo">
                  <span className="font-mono">{textoOVacio(operario.correo)}</span>
                </Dato>
                <Dato label="Cargo">{operario.cargo}</Dato>
                <Dato label="Turno">{etiquetaTurno(operario.turno)}</Dato>
                <Dato label="Almacén">{almacen?.nombre ?? '…'}</Dato>
              </>
            )}
            {proveedor && (
              <>
                <Dato label="Razón social">{proveedor.nombre}</Dato>
                <Dato label="Estado">
                  <StatusBadge estado={proveedor.estado} />
                </Dato>
                <Dato label="RUC">
                  <span className="font-mono">{proveedor.ruc}</span>
                </Dato>
                <Dato label="Correo">
                  <span className="font-mono">{textoOVacio(proveedor.correo)}</span>
                </Dato>
                <Dato label="Teléfono">{textoOVacio(proveedor.telefono)}</Dato>
                <Dato label="Dirección">{textoOVacio(proveedor.direccion)}</Dato>
              </>
            )}
            <Dato label="Empresa">{empresa?.nombre ?? '—'}</Dato>
          </dl>
        </Card>
        <Card padding="md" title="Cambiar contraseña">
          <CambiarPasswordForm onSuccess={() => toast.success('Tu contraseña fue actualizada.', 'Contraseña cambiada')} />
        </Card>
      </div>
    </>
  )
}

function Dato({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="label-stencil">{label}</dt>
      <dd className="mt-0.5 break-words text-fg">{children}</dd>
    </div>
  )
}
