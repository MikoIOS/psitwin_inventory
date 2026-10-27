/**
 * Proveedores de la empresa: lista con búsqueda y filtro por estado, crear/editar (RUC solo al crear),
 * activar/desactivar, eliminar (409 → sugerir desactivar) y detalle con sus órdenes de reposición.
 *
 * El detalle se abre con `?proveedor=<id>` (enlazable).
 */
import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { ApiError } from '@/api/client'
import { ESTADO_PROVEEDOR_OPCIONES } from '@/api/enums'
import { useCreateProveedor, useDeleteProveedor, useProveedores, useUpdateProveedor, useResetPasswordProveedor } from '@/api/proveedores'
import type { EstadoProveedor, Proveedor, ProveedorUpdate } from '@/api/types'
import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  Field,
  Icon,
  Input,
  Modal,
  PageHeader,
  Select,
  StatusBadge,
  useApiErrorHandler,
  useToast,
} from '@/components/ui'
import { formatNumero } from '@/lib/format'
import { ProveedorDetalleModal } from './ProveedorDetalleModal'
import { ProveedorForm, type ProveedorFormOutput } from './ProveedorForm'
import { BadgesCuenta, CredencialesEntregaModal, RestablecerPasswordModal } from '@/components/CredencialesModal'
import { VerificarCorreoModal } from './VerificarCorreoModal'

const FORM_ID = 'form-proveedor'

const norm = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim()

function bodyUpdate(p: Proveedor, cambios: Partial<ProveedorUpdate> = {}): ProveedorUpdate {
  return {
    nombre: p.nombre,
    correo: p.correo ?? null,
    telefono: p.telefono,
    direccion: p.direccion,
    tiempo_entrega_estimado_dias: p.tiempo_entrega_estimado_dias,
    estado: p.estado,
    ...cambios,
  }
}

export default function ProveedoresPage() {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const [params, setParams] = useSearchParams()

  const q = useProveedores()
  const crear = useCreateProveedor()
  const actualizar = useUpdateProveedor()
  const eliminar = useDeleteProveedor()

  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState<EstadoProveedor | ''>('')
  const hayFiltros = !!(busqueda || estado)
  const limpiarFiltros = () => {
    setBusqueda('')
    setEstado('')
  }

  const [form, setForm] = useState<{ modo: 'crear' } | { modo: 'editar'; proveedor: Proveedor } | null>(null)
  const [aEliminar, setAEliminar] = useState<Proveedor | null>(null)
  const [bloqueo, setBloqueo] = useState<{ proveedor: Proveedor; detalle: string } | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const todos = q.data
  const filtrados = todos
    ?.filter((p) => {
      if (estado && p.estado !== estado) return false
      if (busqueda) {
        const b = norm(busqueda)
        return norm(p.nombre).includes(b) || p.ruc.includes(busqueda.trim()) || norm(p.correo ?? '').includes(b)
      }
      return true
    })
    .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  const activos = todos?.filter((p) => p.estado === 'ACTIVO').length ?? 0

  // Detalle (?proveedor=id)
  const idDetalle = params.get('proveedor')
  const detalle = idDetalle ? (todos?.find((p) => p.id_proveedor === idDetalle) ?? null) : null
  const abrirDetalle = (p: Proveedor) =>
    setParams((sp) => {
      sp.set('proveedor', p.id_proveedor)
      return sp
    })
  const cerrarDetalle = () =>
    setParams(
      (sp) => {
        sp.delete('proveedor')
        return sp
      },
      { replace: true },
    )

  /* ---------------------------- Acciones ---------------------------- */

  const resetear = useResetPasswordProveedor()
  const [aRestablecer, setARestablecer] = useState<Proveedor | null>(null)
  const [credenciales, setCredenciales] = useState<{ nombre: string; correo: string; password: string } | null>(null)

  const guardar = async (v: ProveedorFormOutput) => {
    if (form?.modo === 'editar') {
      const { ruc: _ruc, password_temporal: _pw, ...editables } = v // RUC y contraseña no van en el PUT
      await actualizar.mutateAsync({ id: form.proveedor.id_proveedor, body: bodyUpdate(form.proveedor, editables) })
      toast.success(`Se guardaron los cambios de ${v.nombre}.`, 'Proveedor actualizado')
    } else {
      const { password_temporal, ...datos } = v
      await crear.mutateAsync({ ...datos, ...(password_temporal ? { password_temporal } : {}) })
      toast.success(
        v.estado === 'ACTIVO' ? `${v.nombre} ya puede usarse en solicitudes de reposición.` : `${v.nombre} se registró como inactivo.`,
        'Proveedor registrado',
      )
      if (password_temporal && v.correo) setCredenciales({ nombre: v.nombre, correo: v.correo, password: password_temporal })
    }
  }

  const [aVerificar, setAVerificar] = useState<Proveedor | null>(null)
  const toggleEstado = (p: Proveedor) => {
    const nuevo: EstadoProveedor = p.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO'
    setTogglingId(p.id_proveedor)
    actualizar.mutate(
      { id: p.id_proveedor, body: bodyUpdate(p, { estado: nuevo }) },
      {
        onSuccess: () => {
          toast.success(
            nuevo === 'ACTIVO' ? `${p.nombre} vuelve a estar disponible para nuevas órdenes.` : `${p.nombre} ya no aparecerá al crear órdenes.`,
            nuevo === 'ACTIVO' ? 'Proveedor activado' : 'Proveedor desactivado',
          )
          setBloqueo(null)
        },
        onError: (e) => handleError(e, { title: 'No se pudo cambiar el estado' }),
        onSettled: () => setTogglingId(null),
      },
    )
  }

  const confirmarEliminar = () => {
    if (!aEliminar) return
    const p = aEliminar
    eliminar.mutate(p.id_proveedor, {
      onSuccess: () => {
        toast.success(`${p.nombre} fue eliminado.`, 'Proveedor eliminado')
        setAEliminar(null)
        if (idDetalle === p.id_proveedor) cerrarDetalle()
      },
      onError: (e) => {
        setAEliminar(null)
        if (e instanceof ApiError && e.isConflict) {
          setBloqueo({ proveedor: p, detalle: e.detail })
          return
        }
        handleError(e, { title: 'No se pudo eliminar el proveedor' })
      },
    })
  }

  const guardando = crear.isPending || (form?.modo === 'editar' && actualizar.isPending)

  /* ----------------------------- Render ----------------------------- */

  return (
    <>
      <PageHeader
        eyebrow="Reposición"
        title="Proveedores"
        description="Empresas a las que se piden órdenes de reposición. Solo los proveedores activos pueden recibir órdenes nuevas."
        meta={
          todos && (
            <span className="text-sm text-fg-muted">
              <span className="tabular font-semibold text-fg">{activos}</span> de <span className="tabular">{todos.length}</span> proveedores activos
            </span>
          )
        }
        actions={
          <Button icon="plus" onClick={() => setForm({ modo: 'crear' })}>
            Nuevo proveedor
          </Button>
        }
      />

      <Card padding="sm" className="mb-4">
        <div className="grid gap-3 sm:grid-cols-[2fr_1fr_auto] sm:items-end">
          <Field label="Buscar">
            <Input type="search" placeholder="Nombre, RUC o correo" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          </Field>
          <Field label="Estado">
            <Select
              options={ESTADO_PROVEEDOR_OPCIONES}
              placeholder="Todos"
              value={estado}
              onChange={(e) => setEstado(e.target.value as EstadoProveedor | '')}
            />
          </Field>
          <Button variant="ghost" icon="x" onClick={limpiarFiltros} disabled={!hayFiltros}>
            Limpiar
          </Button>
        </div>
      </Card>

      {todos && hayFiltros && (
        <p className="mb-2 text-sm text-fg-muted" aria-live="polite">
          {filtrados?.length ?? 0} de {todos.length} proveedores
        </p>
      )}

      <DataTable
        caption="Proveedores de la empresa"
        data={filtrados}
        loading={q.isLoading}
        error={q.error}
        onRetry={() => void q.refetch()}
        rowKey={(p) => p.id_proveedor}
        onRowClick={abrirDetalle}
        rowClassName={(p) => (p.estado === 'INACTIVO' ? 'opacity-70' : undefined)}
        empty={
          todos && todos.length > 0 ? (
            <EmptyState
              icon="search"
              title="Ningún proveedor coincide"
              description="Prueba con otro nombre, RUC o estado."
              action={
                <Button variant="secondary" size="sm" onClick={limpiarFiltros}>
                  Limpiar filtros
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon="truck"
              title="Aún no hay proveedores"
              description="Registra un proveedor activo para poder crear órdenes de reposición."
              action={
                <Button icon="plus" onClick={() => setForm({ modo: 'crear' })}>
                  Nuevo proveedor
                </Button>
              }
            />
          )
        }
        columns={[
          {
            id: 'nombre',
            header: 'Proveedor',
            mobile: 'title',
            cell: (p) => (
              <span className="block min-w-0">
                <span className="block truncate font-medium text-fg">{p.nombre}</span>
                <span className="block truncate text-xs font-normal text-fg-muted">
                  {p.correo}
                  {p.correo ? (p.correo_verificado ? ' · verificado' : ' · sin verificar') : 'Sin correo'}
                </span>
                <span className="mt-0.5 flex flex-wrap gap-1 empty:hidden">
                  <BadgesCuenta cuenta={p} />
                </span>
              </span>
            ),
          },
          { id: 'estado', header: 'Estado', cell: (p) => <StatusBadge estado={p.estado} />, mobile: 'badge' },
          { id: 'ruc', header: 'RUC', cell: (p) => <span className="font-mono">{p.ruc}</span> },
          { id: 'telefono', header: 'Teléfono', cell: (p) => <span className="tabular">{p.telefono ?? '—'}</span> },
          {
            id: 'entrega',
            header: 'Entrega',
            align: 'right',
            cell: (p) => `${formatNumero(p.tiempo_entrega_estimado_dias)} ${p.tiempo_entrega_estimado_dias === 1 ? 'día' : 'días'}`,
          },
        ]}
        actions={(p) => (
          <>
            {p.correo && !p.correo_verificado && (
              <Button size="sm" variant="ghost" onClick={() => setAVerificar(p)}>
                Verificar correo
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              icon={p.estado === 'ACTIVO' ? 'x' : 'check'}
              loading={togglingId === p.id_proveedor}
              onClick={() => toggleEstado(p)}
              aria-label={`${p.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'} ${p.nombre}`}
            >
              {p.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              icon="key"
              iconOnly
              aria-label={`${p.tiene_cuenta === false ? 'Dar acceso a' : 'Restablecer contraseña de'} ${p.nombre}`}
              title={p.tiene_cuenta === false ? 'Dar acceso' : 'Restablecer contraseña'}
              onClick={() => setARestablecer(p)}
            />
            <Button size="sm" variant="ghost" icon="edit" iconOnly aria-label={`Editar ${p.nombre}`} onClick={() => setForm({ modo: 'editar', proveedor: p })} />
            <Button size="sm" variant="ghost" icon="trash" iconOnly aria-label={`Eliminar ${p.nombre}`} onClick={() => setAEliminar(p)} className="text-danger hover:text-danger" />
          </>
        )}
      />

      <VerificarCorreoModal proveedor={aVerificar} onClose={() => setAVerificar(null)} />
      <RestablecerPasswordModal
        cuenta={aRestablecer ? { id: aRestablecer.id_proveedor, nombre: aRestablecer.nombre, correo: aRestablecer.correo, tiene_cuenta: aRestablecer.tiene_cuenta } : null}
        onReset={(id, body) => resetear.mutateAsync({ id, body })}
        onClose={() => setARestablecer(null)}
      />
      <CredencialesEntregaModal datos={credenciales} onClose={() => setCredenciales(null)} />

      {/* Crear / editar */}
      <Modal
        open={!!form}
        onClose={() => setForm(null)}
        dismissable={!guardando}
        size="lg"
        title={form?.modo === 'editar' ? 'Editar proveedor' : 'Nuevo proveedor'}
        description={form?.modo === 'editar' ? `RUC ${form.proveedor.ruc}` : 'Datos de contacto y condiciones de entrega.'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setForm(null)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" form={FORM_ID} loading={guardando}>
              {form?.modo === 'editar' ? 'Guardar cambios' : 'Registrar proveedor'}
            </Button>
          </>
        }
      >
        {form && (
          <ProveedorForm
            key={form.modo === 'editar' ? form.proveedor.id_proveedor : 'nuevo'}
            formId={FORM_ID}
            hideActions
            proveedor={form.modo === 'editar' ? form.proveedor : null}
            onSubmit={guardar}
            onSuccess={() => setForm(null)}
          />
        )}
      </Modal>

      {/* Detalle */}
      <ProveedorDetalleModal
        proveedor={detalle}
        onClose={cerrarDetalle}
        onEditar={(p) => setForm({ modo: 'editar', proveedor: p })}
        onToggleEstado={toggleEstado}
        toggling={!!detalle && togglingId === detalle.id_proveedor}
      />

      {/* Eliminar */}
      <ConfirmDialog
        open={!!aEliminar}
        tone="danger"
        title="Eliminar proveedor"
        confirmLabel="Eliminar"
        loading={eliminar.isPending}
        description={
          aEliminar && (
            <>
              ¿Eliminar a <strong className="text-fg">{aEliminar.nombre}</strong> (RUC <span className="font-mono">{aEliminar.ruc}</span>)? Esta
              acción no se puede deshacer. Si tiene órdenes de reposición, es preferible <strong className="text-fg">desactivarlo</strong>.
            </>
          )
        }
        onConfirm={confirmarEliminar}
        onCancel={() => setAEliminar(null)}
      />

      {/* 409 al eliminar: sugerir desactivar */}
      <Modal
        open={!!bloqueo}
        onClose={() => setBloqueo(null)}
        size="sm"
        title="No se puede eliminar"
        footer={
          bloqueo && (
            <>
              <Button variant="secondary" onClick={() => setBloqueo(null)}>
                Cerrar
              </Button>
              {bloqueo.proveedor.estado === 'ACTIVO' && (
                <Button icon="x" loading={togglingId === bloqueo.proveedor.id_proveedor} onClick={() => toggleEstado(bloqueo.proveedor)}>
                  Desactivar en su lugar
                </Button>
              )}
            </>
          )
        }
      >
        {bloqueo && (
          <div className="flex gap-3 text-sm">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-warning-soft text-warning">
              <Icon name="alert" className="size-5" />
            </span>
            <div className="flex flex-col gap-2 text-fg-muted">
              <p className="text-fg">{bloqueo.detalle}</p>
              <p>
                {bloqueo.proveedor.estado === 'ACTIVO'
                  ? `Puedes desactivar a ${bloqueo.proveedor.nombre}: dejará de aparecer al crear órdenes, pero se conservan sus órdenes existentes.`
                  : `${bloqueo.proveedor.nombre} ya está inactivo y no aparecerá al crear órdenes. Sus órdenes existentes se conservan.`}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
