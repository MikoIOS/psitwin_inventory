/**
 * Operarios (solo EMPRESA): cuentas de acceso del personal de almacén. Cada operario tiene correo + contraseña
 * (temporal al crearla o restablecerla: la cambia en su primer ingreso) y un almacén: solo ve ese almacén.
 * Acciones: registrar, editar, activar / desactivar, restablecer contraseña («Dar acceso» si no tiene cuenta) y eliminar.
 *
 * El detalle se abre con `?operario=<id>` (enlazable).
 */
import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { useAlmacenes } from '@/api/almacenes'
import { ApiError } from '@/api/client'
import { ESTADO_OPERARIO_OPCIONES, etiquetaTurno, operarioActivo, TURNO_OPCIONES } from '@/api/enums'
import { useCreateOperario, useDeleteOperario, useOperarios, useResetPasswordOperario, useUpdateOperario } from '@/api/operarios'
import type { EstadoOperario, Operario, OperarioUpdate, TurnoOperario } from '@/api/types'
import { AlmacenSelect } from '@/components/selects'
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
import { BadgesCuenta, CredencialesEntregaModal, RestablecerPasswordModal } from '@/components/CredencialesModal'
import { OperarioDetalleModal } from './OperarioDetalleModal'
import { OperarioForm, type OperarioFormOutput } from './OperarioForm'

const FORM_ID = 'form-operario'

/** Normaliza para búsqueda sin tildes ni mayúsculas. */
const norm = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim()

function nombreCompleto(o: Pick<Operario, 'nombre' | 'apellido'>) {
  return `${o.nombre} ${o.apellido}`
}

function bodyUpdate(o: Operario, cambios: Partial<OperarioUpdate> = {}): OperarioUpdate {
  return { nombre: o.nombre, apellido: o.apellido, cargo: o.cargo, turno: o.turno, estado: o.estado, ...cambios }
}

export default function OperariosPage() {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const [params, setParams] = useSearchParams()

  const q = useOperarios()
  const almacenesQ = useAlmacenes()
  const crear = useCreateOperario()
  const actualizar = useUpdateOperario()
  const eliminar = useDeleteOperario()

  // Filtros
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState<EstadoOperario | ''>('')
  const [turno, setTurno] = useState<TurnoOperario | ''>('')
  const [idAlmacen, setIdAlmacen] = useState('')
  const hayFiltros = !!(busqueda || estado || turno || idAlmacen)
  const limpiarFiltros = () => {
    setBusqueda('')
    setEstado('')
    setTurno('')
    setIdAlmacen('')
  }

  // Modales
  const [form, setForm] = useState<{ modo: 'crear' } | { modo: 'editar'; operario: Operario } | null>(null)
  const [aEliminar, setAEliminar] = useState<Operario | null>(null)
  const [bloqueo, setBloqueo] = useState<{ operario: Operario; detalle: string } | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  /** Operarios antiguos pueden no tener almacén asignado. */
  const nombreAlmacen = (id: string | null | undefined) =>
    id ? (almacenesQ.data?.find((a) => a.id_almacen === id)?.nombre ?? '—') : 'Sin almacén'

  const todos = q.data
  const filtrados = todos
    ?.filter((o) => {
      if (estado && o.estado.toUpperCase() !== estado) return false
      if (turno && o.turno !== turno) return false
      if (idAlmacen && o.id_almacen !== idAlmacen) return false
      if (busqueda) {
        const b = norm(busqueda)
        if (!norm(`${o.nombre} ${o.apellido}`).includes(b) && !norm(`${o.apellido} ${o.nombre}`).includes(b)) return false
      }
      return true
    })
    .sort((a, b) => a.apellido.localeCompare(b.apellido, 'es') || a.nombre.localeCompare(b.nombre, 'es'))

  const activos = todos?.filter((o) => operarioActivo(o.estado)).length ?? 0

  // Detalle (?operario=id)
  const idDetalle = params.get('operario')
  const detalle = idDetalle ? (todos?.find((o) => o.id_operario === idDetalle) ?? null) : null
  const abrirDetalle = (o: Operario) =>
    setParams((p) => {
      p.set('operario', o.id_operario)
      return p
    })
  const cerrarDetalle = () =>
    setParams(
      (p) => {
        p.delete('operario')
        return p
      },
      { replace: true },
    )

  /* ---------------------------- Acciones ---------------------------- */

  const resetear = useResetPasswordOperario()
  const [aRestablecer, setARestablecer] = useState<Operario | null>(null)
  const [credenciales, setCredenciales] = useState<{ nombre: string; correo: string; password: string } | null>(null)

  const guardar = async (v: OperarioFormOutput) => {
    if (form?.modo === 'editar') {
      const o = form.operario
      const body = bodyUpdate(o, {
        nombre: v.nombre,
        apellido: v.apellido,
        cargo: v.cargo,
        turno: v.turno,
        estado: v.estado,
        id_almacen: v.id_almacen,
        ...(v.correo ? { correo: v.correo } : {}),
      })
      await actualizar.mutateAsync({ id: o.id_operario, body })
      toast.success(`${nombreCompleto(v)} fue actualizado.`, 'Operario actualizado')
    } else {
      await crear.mutateAsync(v)
      toast.success(`${nombreCompleto(v)} ya puede iniciar sesión.`, 'Operario registrado')
      setCredenciales({ nombre: nombreCompleto(v), correo: v.correo, password: v.password_temporal })
    }
  }

  const toggleEstado = (o: Operario) => {
    const nuevo: EstadoOperario = operarioActivo(o.estado) ? 'INACTIVO' : 'ACTIVO'
    setTogglingId(o.id_operario)
    actualizar.mutate(
      { id: o.id_operario, body: bodyUpdate(o, { estado: nuevo }) },
      {
        onSuccess: () => {
          toast.success(
            nuevo === 'ACTIVO'
              ? `${nombreCompleto(o)} vuelve a estar disponible para operaciones.`
              : `${nombreCompleto(o)} ya no aparecerá en recepciones ni movimientos.`,
            nuevo === 'ACTIVO' ? 'Operario activado' : 'Operario desactivado',
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
    const o = aEliminar
    eliminar.mutate(o.id_operario, {
      onSuccess: () => {
        toast.success(`${nombreCompleto(o)} fue eliminado.`, 'Operario eliminado')
        setAEliminar(null)
        if (idDetalle === o.id_operario) cerrarDetalle()
      },
      onError: (e) => {
        setAEliminar(null)
        if (e instanceof ApiError && e.isConflict) {
          setBloqueo({ operario: o, detalle: e.detail })
          return
        }
        handleError(e, { title: 'No se pudo eliminar el operario' })
      },
    })
  }

  /* ----------------------------- Render ----------------------------- */

  const guardando = crear.isPending || (form?.modo === 'editar' && actualizar.isPending)

  return (
    <>
      <PageHeader
        eyebrow="Personal · Administración"
        title="Operarios"
        description="Cuentas del personal de almacén. Cada operario inicia sesión y trabaja solo en su almacén."
        meta={
          todos && (
            <span className="text-sm text-fg-muted">
              <span className="tabular font-semibold text-fg">{activos}</span> de <span className="tabular">{todos.length}</span> operarios activos
            </span>
          )
        }
        actions={
          <Button icon="plus" onClick={() => setForm({ modo: 'crear' })}>
            Registrar operario
          </Button>
        }
      />

      <Card padding="sm" className="mb-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[2fr_1.4fr_1fr_1fr_auto] lg:items-end">
          <Field label="Buscar">
            <Input type="search" placeholder="Nombre o apellido" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          </Field>
          <Field label="Almacén">
            <AlmacenSelect placeholder="Todos los almacenes" value={idAlmacen} onChange={(e) => setIdAlmacen(e.target.value)} />
          </Field>
          <Field label="Estado">
            <Select
              options={ESTADO_OPERARIO_OPCIONES}
              placeholder="Todos"
              value={estado}
              onChange={(e) => setEstado(e.target.value as EstadoOperario | '')}
            />
          </Field>
          <Field label="Turno">
            <Select options={TURNO_OPCIONES} placeholder="Todos" value={turno} onChange={(e) => setTurno(e.target.value as TurnoOperario | '')} />
          </Field>
          <Button variant="ghost" icon="x" onClick={limpiarFiltros} disabled={!hayFiltros} className="sm:col-span-2 lg:col-span-1">
            Limpiar
          </Button>
        </div>
      </Card>

      {todos && hayFiltros && (
        <p className="mb-2 text-sm text-fg-muted" aria-live="polite">
          {filtrados?.length ?? 0} de {todos.length} operarios
        </p>
      )}

      <DataTable
        caption="Operarios de la empresa"
        data={filtrados}
        loading={q.isLoading}
        error={q.error}
        onRetry={() => void q.refetch()}
        rowKey={(o) => o.id_operario}
        onRowClick={abrirDetalle}
        rowClassName={(o) => (!operarioActivo(o.estado) ? 'opacity-70' : undefined)}
        empty={
          todos && todos.length > 0 ? (
            <EmptyState
              icon="search"
              title="Ningún operario coincide"
              description="Prueba con otros filtros o términos de búsqueda."
              action={
                <Button variant="secondary" size="sm" onClick={limpiarFiltros}>
                  Limpiar filtros
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon="users"
              title="Aún no hay operarios"
              description="Crea la cuenta de cada operario: verá su almacén, pedirá reposición y registrará recepciones y salidas."
              action={
                <Button icon="plus" onClick={() => setForm({ modo: 'crear' })}>
                  Registrar operario
                </Button>
              }
            />
          )
        }
        columns={[
          {
            id: 'nombre',
            header: 'Operario',
            mobile: 'title',
            cell: (o) => (
              <span className="flex items-center gap-2.5">
                <span
                  aria-hidden="true"
                  className="hidden size-8 shrink-0 items-center justify-center rounded-full bg-surface-2 font-mono text-xs font-semibold text-fg-muted sm:flex"
                >
                  {(o.nombre[0] ?? '').toUpperCase()}
                  {(o.apellido[0] ?? '').toUpperCase()}
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-medium text-fg">
                    {o.apellido}, {o.nombre}
                  </span>
                  {o.correo && <span className="block truncate font-mono text-xs text-fg-muted">{o.correo}</span>}
                  <span className="mt-0.5 flex flex-wrap gap-1 empty:hidden">
                    <BadgesCuenta cuenta={o} />
                  </span>
                </span>
              </span>
            ),
          },
          { id: 'estado', header: 'Estado', cell: (o) => <StatusBadge estado={o.estado} />, mobile: 'badge' },
          { id: 'cargo', header: 'Cargo', cell: (o) => o.cargo },
          {
            id: 'almacen',
            header: 'Almacén',
            cell: (o: Operario) => (o.id_almacen ? nombreAlmacen(o.id_almacen) : <span className="text-warning">Sin almacén</span>),
          },
          { id: 'turno', header: 'Turno', cell: (o) => etiquetaTurno(o.turno) },
        ]}
        actions={(o) => (
          <>
            <Button
              size="sm"
              variant="ghost"
              icon={operarioActivo(o.estado) ? 'x' : 'check'}
              loading={togglingId === o.id_operario}
              onClick={() => toggleEstado(o)}
              aria-label={`${operarioActivo(o.estado) ? 'Desactivar' : 'Activar'} a ${nombreCompleto(o)}`}
            >
              {operarioActivo(o.estado) ? 'Desactivar' : 'Activar'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              icon="key"
              iconOnly
              aria-label={`${o.tiene_cuenta === false ? 'Dar acceso a' : 'Restablecer contraseña de'} ${nombreCompleto(o)}`}
              title={o.tiene_cuenta === false ? 'Dar acceso' : 'Restablecer contraseña'}
              onClick={() => setARestablecer(o)}
            />
            <Button size="sm" variant="ghost" icon="edit" iconOnly aria-label={`Editar a ${nombreCompleto(o)}`} onClick={() => setForm({ modo: 'editar', operario: o })} />
            <Button size="sm" variant="ghost" icon="trash" iconOnly aria-label={`Eliminar a ${nombreCompleto(o)}`} onClick={() => setAEliminar(o)} className="text-danger hover:text-danger" />
          </>
        )}
      />

      {/* Crear / editar */}
      <Modal
        open={!!form}
        onClose={() => setForm(null)}
        dismissable={!guardando}
        size="lg"
        title={form?.modo === 'editar' ? 'Editar operario' : 'Registrar operario'}
        description={form?.modo === 'editar' ? 'La contraseña no se cambia aquí: usa «Restablecer contraseña».' : 'El operario iniciará sesión con este correo y la contraseña temporal.'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setForm(null)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" form={FORM_ID} loading={guardando}>
              {form?.modo === 'editar' ? 'Guardar cambios' : 'Registrar operario'}
            </Button>
          </>
        }
      >
        {form && (
          <OperarioForm
            key={form.modo === 'editar' ? form.operario.id_operario : 'nuevo'}
            formId={FORM_ID}
            hideActions
            operario={form.modo === 'editar' ? form.operario : null}
            idAlmacenInicial={idAlmacen || undefined}
            onSubmit={guardar}
            onSuccess={() => setForm(null)}
          />
        )}
      </Modal>

      {/* Detalle */}
      <OperarioDetalleModal
        operario={detalle}
        nombreAlmacen={detalle ? nombreAlmacen(detalle.id_almacen) : ''}
        onClose={cerrarDetalle}
        onEditar={(o) => setForm({ modo: 'editar', operario: o })}
        onToggleEstado={toggleEstado}
        toggling={!!detalle && togglingId === detalle.id_operario}
      />

      <RestablecerPasswordModal
        cuenta={aRestablecer ? { id: aRestablecer.id_operario, nombre: nombreCompleto(aRestablecer), correo: aRestablecer.correo, tiene_cuenta: aRestablecer.tiene_cuenta } : null}
        onReset={(id, body) => resetear.mutateAsync({ id, body })}
        onClose={() => setARestablecer(null)}
      />
      <CredencialesEntregaModal datos={credenciales} onClose={() => setCredenciales(null)} />

      {/* Eliminar */}
      <ConfirmDialog
        open={!!aEliminar}
        tone="danger"
        title="Eliminar operario"
        confirmLabel="Eliminar"
        loading={eliminar.isPending}
        description={
          aEliminar && (
            <>
              ¿Eliminar a <strong className="text-fg">{nombreCompleto(aEliminar)}</strong>? Esta acción no se puede deshacer. Si tiene
              movimientos o recepciones registradas, es preferible <strong className="text-fg">desactivarlo</strong> para conservar el historial.
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
              {operarioActivo(bloqueo.operario.estado) && (
                <Button icon="x" loading={togglingId === bloqueo.operario.id_operario} onClick={() => toggleEstado(bloqueo.operario)}>
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
                {operarioActivo(bloqueo.operario.estado)
                  ? `Puedes desactivar a ${nombreCompleto(bloqueo.operario)}: dejará de aparecer en recepciones y movimientos, pero se conservará su historial.`
                  : `${nombreCompleto(bloqueo.operario)} ya está inactivo, por lo que no aparecerá en nuevas operaciones. Su historial se conserva.`}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
