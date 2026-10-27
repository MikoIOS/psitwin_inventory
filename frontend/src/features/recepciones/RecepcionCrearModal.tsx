/**
 * Registrar una recepción de mercadería en UN SOLO PASO (solo OPERARIO; el autor sale de su token).
 *
 * `POST /recepciones` crea la recepción e ingresa cada línea al inventario (detalle + movimiento
 * ENTRADA/RECEPCION + estado de la orden PARCIAL / RECIBIDA).
 *  - Parte del DESPACHO del proveedor si existe: precarga cantidad, vencimiento y temperatura de cada línea.
 *  - Rack de destino por línea: `GET /racks/disponibles?id_almacen=&id_producto=&cantidad=` (racks DISPONIBLES donde
 *    cabe por kg y temperatura), primero los que ya tienen el producto. Al enviar se usa el inventario del producto
 *    en ese rack o, si no existe, se crea (stock 0, mín/máx editables).
 *  - Por línea: recibida, rechazadas (parcial), estado CONFORME / RECHAZADO (no ingresa nada) / EN_EVALUACION
 *    (se resuelve luego en el detalle de la recepción), vencimiento, temperatura (obligatoria y dentro del rango del
 *    producto si es refrigerado) y comentario (obligatorio si hay rechazo o no es conforme).
 *  - 409 (kg, estado o temperatura del rack; sobre-recepción): se muestra en el modal y se refrescan los racks.
 *    La sobre-recepción además se bloquea aquí antes de enviar.
 *
 * Solo órdenes ENVIADA / PARCIAL del almacén del operario. Si se pasa `orden`, queda fija.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Controller, useFieldArray, useForm, useWatch, type Control, type FieldErrors, type UseFormRegister, type UseFormSetValue } from 'react-hook-form'
import { z } from 'zod'
import { ApiError } from '@/api/client'
import { ACCIONES_ORDEN, ESTADO_RECEPCION_OPCIONES } from '@/api/enums'
import { useDetallesReposicion, useOrdenes } from '@/api/ordenesReposicion'
import { inventariosApi, useCreateInventario, useInventarios } from '@/api/inventarios'
import { useProductos } from '@/api/productos'
import { queryKeys } from '@/api/queryKeys'
import { useRacksDisponibles } from '@/api/racks'
import { useCreateRecepcion, useDetallesRecepcionPorOrden } from '@/api/recepciones'
import type { DetalleRecepcionCreate, EstadoRecepcion, OrdenReposicion, RecepcionMercaderia } from '@/api/types'
import { Button, Checkbox, EmptyState, ErrorState, Field, Input, LoadingBlock, Modal, Select, StatusBadge, Textarea, useToast } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'
import { calcularPendientes, type LineaPendiente } from '@/lib/ordenes'
import { temperaturaRack } from '@/lib/racks'
import { textoOpcional } from '@/lib/zod'
import { ApiErrorAlert, FormAlert, useInlineApiError } from '@/features/inventario/formUtils'
import { codigoOrden, useNombres } from '@/features/ordenes/useNombres'

const FORM_ID = 'form-recepcion-crear'
const ESTADOS = ['CONFORME', 'RECHAZADO', 'EN_EVALUACION'] as const satisfies readonly EstadoRecepcion[]

const num = (v: string) => (v.trim() === '' ? NaN : Number(v.trim().replace(',', '.')))

/** Unidades que deben caber en el rack: lo aceptado (EN_EVALUACION reserva lo recibido; RECHAZADO no ocupa). */
function unidadesAUbicar(l: Pick<LineaIn, 'cantidad_recibida' | 'cantidad_rechazada' | 'estado_recepcion'>): number {
  const rec = num(l.cantidad_recibida)
  if (!Number.isFinite(rec) || rec <= 0 || l.estado_recepcion === 'RECHAZADO') return 0
  const rech = l.estado_recepcion === 'CONFORME' ? num(l.cantidad_rechazada) : 0
  return Math.max(0, rec - (Number.isFinite(rech) ? rech : 0))
}

const lineaSchema = z
  .object({
    id_detalle_reposicion: z.string(),
    incluir: z.boolean(),
    cantidad_recibida: z.string(),
    cantidad_rechazada: z.string(),
    id_rack: z.string(),
    /** Solo se usan si hay que crear el inventario del producto en el rack elegido. */
    stock_minimo: z.string(),
    stock_maximo: z.string(),
    fecha_vencimiento: z.string(),
    temperatura_recepcion: z.string(),
    estado_recepcion: z.enum(ESTADOS),
    comentario_recepcion: z.string(),
  })
  .superRefine((l, ctx) => {
    if (!l.incluir) return
    const issue = (path: string, message: string) => ctx.addIssue({ code: 'custom', path: [path], message })
    const cant = num(l.cantidad_recibida)
    if (!Number.isInteger(cant) || cant <= 0) issue('cantidad_recibida', 'Entero mayor que 0')
    const rech = num(l.cantidad_rechazada)
    const hayRechazo = l.estado_recepcion === 'CONFORME' && rech > 0
    if (l.estado_recepcion === 'CONFORME' && (!Number.isInteger(rech) || rech < 0 || rech > cant)) issue('cantidad_rechazada', 'Entero entre 0 y lo recibido')
    if (!l.id_rack) issue('id_rack', 'Elige el rack de destino')
    const t = l.temperatura_recepcion.trim()
    if (t !== '' && !Number.isFinite(num(t))) issue('temperatura_recepcion', 'Número no válido')
    if ((l.estado_recepcion !== 'CONFORME' || hayRechazo) && l.comentario_recepcion.trim() === '') {
      issue('comentario_recepcion', 'Indica el motivo (obligatorio si hay rechazo o no es conforme)')
    }
    if (l.comentario_recepcion.trim().length > 1000) issue('comentario_recepcion', 'Máximo 1000 caracteres')
    const mi = num(l.stock_minimo)
    const ma = num(l.stock_maximo)
    if (l.stock_minimo.trim() !== '' && (!Number.isInteger(mi) || mi < 0)) issue('stock_minimo', 'Entero ≥ 0')
    if (l.stock_maximo.trim() !== '' && (!Number.isInteger(ma) || ma < 0 || (Number.isInteger(mi) && ma < mi))) issue('stock_maximo', 'Entero ≥ al mínimo')
  })

const schema = z
  .object({
    observaciones_generales: textoOpcional({ max: 1000 }),
    lineas: z.array(lineaSchema),
  })
  .refine((v) => v.lineas.some((l) => l.incluir), { path: ['root'], message: 'Marca al menos un producto recibido' })

type In = z.input<typeof schema>
type Out = z.output<typeof schema>
type LineaIn = In['lineas'][number]

/** "2026-10-01" (input date, hora local) → ISO. */
function fechaAIso(v: string): string | null {
  if (!v) return null
  const d = new Date(`${v}T00:00:00`)
  return Number.isNaN(d.getTime()) ? null : d.toISOString()
}

function aDetalleCreate(l: LineaIn, idInventario: string): DetalleRecepcionCreate {
  const t = l.temperatura_recepcion.trim()
  const comentario = l.comentario_recepcion.trim() || null
  const recibida = num(l.cantidad_recibida)
  // RECHAZADO = no se acepta nada; EN_EVALUACION = aún no se decide (se resuelve después).
  const rechazada = l.estado_recepcion === 'RECHAZADO' ? recibida : l.estado_recepcion === 'CONFORME' ? num(l.cantidad_rechazada) : 0
  return {
    id_detalle_reposicion: l.id_detalle_reposicion,
    id_inventario: idInventario,
    cantidad_recibida: recibida,
    cantidad_rechazada: rechazada,
    motivo_rechazo: rechazada > 0 ? comentario : null,
    fecha_vencimiento: fechaAIso(l.fecha_vencimiento),
    temperatura_recepcion: t === '' ? null : num(t),
    estado_recepcion: l.estado_recepcion,
    comentario_recepcion: comentario,
  }
}

/** Mínimo / máximo sugeridos para un inventario nuevo (editables). */
function sugerirMinMax(unidades: number) {
  const minimo = Math.max(1, Math.round(unidades * 0.2))
  return { minimo: String(minimo), maximo: String(Math.max(minimo, unidades * 2)) }
}

/* ------------------------------------------------------------------ */

export interface RecepcionCrearModalProps {
  open: boolean
  onClose: () => void
  /** Orden fija (desde el detalle de la orden). */
  orden?: OrdenReposicion | undefined
  /** Orden preseleccionada por id (ej. `?orden=<id>`). */
  idOrdenInicial?: string | undefined
  onCreated: (recepcion: RecepcionMercaderia) => void
}

export function RecepcionCrearModal({ open, onClose, orden, idOrdenInicial, onCreated }: RecepcionCrearModalProps) {
  const crear = useCreateRecepcion()
  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!crear.isPending}
      size="xl"
      title="Registrar recepción"
      description="Registra lo que llegó y en qué rack se guarda. Al confirmar, lo aceptado ingresa al inventario."
      footer={
        <>
          <Button variant="secondary" size="lg" className="sm:h-10 sm:text-sm" onClick={onClose} disabled={crear.isPending}>
            Cancelar
          </Button>
          <Button type="submit" form={FORM_ID} size="lg" className="sm:h-10 sm:text-sm" icon="inbox" loading={crear.isPending}>
            Registrar recepción
          </Button>
        </>
      }
    >
      {open && <RecepcionFormGate crear={crear} orden={orden} idOrdenInicial={idOrdenInicial} onCreated={onCreated} />}
    </Modal>
  )
}

interface GateProps {
  crear: ReturnType<typeof useCreateRecepcion>
  orden: OrdenReposicion | undefined
  idOrdenInicial: string | undefined
  onCreated: (r: RecepcionMercaderia) => void
}

/** Espera a que carguen las órdenes para que la preselección (`idOrdenInicial`) no se pierda. */
function RecepcionFormGate(props: GateProps) {
  const ordenesQ = useOrdenes()
  if (!props.orden && ordenesQ.isLoading) return <LoadingBlock label="Cargando órdenes…" className="py-8" />
  if (!props.orden && ordenesQ.error && !ordenesQ.data) return <ErrorState error={ordenesQ.error} onRetry={() => void ordenesQ.refetch()} />
  const recibibles = (ordenesQ.data ?? [])
    .filter((o) => ACCIONES_ORDEN.puedeRecibir(o.estado))
    .sort((a, b) => (a.fecha_estimada_recepcion ?? '').localeCompare(b.fecha_estimada_recepcion ?? ''))
  return <SelectorOrden {...props} recibibles={recibibles} />
}

function SelectorOrden({ crear, orden, idOrdenInicial, onCreated, recibibles }: GateProps & { recibibles: OrdenReposicion[] }) {
  const nombres = useNombres()
  const inicial = orden?.id_orden_reposicion ?? (recibibles.some((o) => o.id_orden_reposicion === idOrdenInicial) ? idOrdenInicial : '')
  const [idOrden, setIdOrden] = useState(inicial ?? '')
  const [faltaOrden, setFaltaOrden] = useState(false)
  const ordenSel = orden ?? recibibles.find((o) => o.id_orden_reposicion === idOrden)

  const opcionesOrden = recibibles.map((o) => ({
    value: o.id_orden_reposicion,
    label: `${codigoOrden(o)} · ${nombres.proveedor(o.id_proveedor)} → ${nombres.almacen(o.id_almacen)}${o.estado === 'PARCIAL' ? ' (parcial)' : ''}`,
  }))

  return (
    <div className="flex flex-col gap-4">
      {orden ? (
        <div className="rounded-[var(--radius-ui)] border border-border bg-surface-2 p-3 text-sm">
          <p className="label-stencil mb-1">Orden</p>
          <p className="flex flex-wrap items-center gap-2">
            <span className="font-mono font-semibold">{codigoOrden(orden)}</span>
            <StatusBadge estado={orden.estado} />
          </p>
          <p className="mt-1 text-fg-muted">
            {nombres.proveedor(orden.id_proveedor)} → {nombres.almacen(orden.id_almacen)}
          </p>
        </div>
      ) : (
        <Field
          label="Orden"
          error={faltaOrden && !ordenSel ? 'Elige una orden enviada o parcial' : undefined}
          hint="Solo órdenes enviadas o con recepción parcial."
          required
        >
          {recibibles.length === 0 ? (
            <Select size="lg" disabled placeholder="No hay órdenes enviadas pendientes de recibir" />
          ) : (
            <Select size="lg" options={opcionesOrden} value={idOrden} onChange={(e) => setIdOrden(e.target.value)} />
          )}
        </Field>
      )}

      {ordenSel ? (
        <LineasGate key={ordenSel.id_orden_reposicion} crear={crear} orden={ordenSel} onCreated={onCreated} />
      ) : (
        // Formulario vacío para que el botón del pie avise que falta la orden.
        <form
          id={FORM_ID}
          noValidate
          onSubmit={(e) => {
            e.preventDefault()
            setFaltaOrden(true)
          }}
        />
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */

function LineasGate({ crear, orden, onCreated }: { crear: GateProps['crear']; orden: OrdenReposicion; onCreated: GateProps['onCreated'] }) {
  const detallesQ = useDetallesReposicion(orden.id_orden_reposicion)
  const recibidosQ = useDetallesRecepcionPorOrden(orden.id_orden_reposicion)
  if (detallesQ.isLoading || recibidosQ.isLoading) return <LoadingBlock label="Cargando productos de la orden…" className="py-8" />
  if (detallesQ.error) return <ErrorState error={detallesQ.error} onRetry={() => void detallesQ.refetch()} />
  if (recibidosQ.error) return <ErrorState title="No se pudo calcular lo pendiente" error={recibidosQ.error} onRetry={() => void recibidosQ.refetch()} />
  const pendientes = calcularPendientes(detallesQ.data ?? [], recibidosQ.data ?? []).filter((l) => l.pendiente > 0)
  if (pendientes.length === 0) {
    return <EmptyState compact icon="check-circle" title="Nada pendiente" description="Todas las líneas de esta orden ya fueron recibidas." />
  }
  return <RecepcionForm crear={crear} orden={orden} pendientes={pendientes} onCreated={onCreated} />
}

function RecepcionForm({
  crear,
  orden,
  pendientes,
  onCreated,
}: {
  crear: GateProps['crear']
  orden: OrdenReposicion
  pendientes: LineaPendiente[]
  onCreated: GateProps['onCreated']
}) {
  const toast = useToast()
  const qc = useQueryClient()
  const crearInv = useCreateInventario()
  const apiError = useInlineApiError()
  const nombres = useNombres()
  const productos = useProductos().data

  const form = useForm<In, unknown, Out>({
    resolver: zodResolver(schema),
    defaultValues: {
      observaciones_generales: '',
      // Si el proveedor registró su despacho, se parte de sus datos (cantidad, vencimiento, temperatura).
      lineas: pendientes.map((l) => {
        const d = orden.despacho?.lineas.find((x) => x.id_detalle_reposicion === l.detalle.id_detalle_reposicion)
        return {
        id_detalle_reposicion: l.detalle.id_detalle_reposicion,
        incluir: true,
        cantidad_recibida: String(d && d.cantidad > 0 ? Math.min(d.cantidad, l.pendiente) : l.pendiente),
        cantidad_rechazada: '0',
        id_rack: '',
        stock_minimo: '',
        stock_maximo: '',
        fecha_vencimiento: d?.fecha_vencimiento?.slice(0, 10) ?? '',
        temperatura_recepcion: d?.temperatura === null || d?.temperatura === undefined ? '' : String(d.temperatura),
        estado_recepcion: 'CONFORME' as const,
        comentario_recepcion: '',
        }
      }),
    },
  })
  const { register, handleSubmit, formState, control, trigger, setValue } = form
  const { fields } = useFieldArray({ control, name: 'lineas' })
  const err = formState.errors
  const errorRaiz = (err as FieldErrors<In> & { root?: { message?: string } }).root?.message

  const submit = handleSubmit(async (v) => {
    apiError.clear()
    // Sobre-recepción: se valida aquí porque el backend crea la recepción antes que sus detalles (un 409 la deja vacía).
    let excede = false
    v.lineas.forEach((l, i) => {
      const p = pendientes[i]
      if (!l.incluir || !p || l.estado_recepcion === 'RECHAZADO' || unidadesAUbicar(l) <= p.pendiente) return
      excede = true
      form.setError(`lineas.${i}.cantidad_recibida`, { message: `Lo aceptado supera lo pendiente (${formatNumero(p.pendiente)})` }, { shouldFocus: true })
    })
    if (excede) return
    // Temperatura: obligatoria en productos refrigerados y, para aceptar la línea, dentro del rango del producto.
    let tempMal = false
    v.lineas.forEach((l, i) => {
      const prod = productos?.find((x) => x.id_producto === pendientes[i]?.detalle.id_producto)
      if (!l.incluir || !prod?.requiere_refrigeracion) return
      const t = l.temperatura_recepcion.trim()
      const min = prod.temperatura_min_almacenamiento
      const max = prod.temperatura_max_almacenamiento
      const fuera = t !== '' && ((min != null && num(t) < min) || (max != null && num(t) > max))
      const mensaje =
        t === ''
          ? 'Obligatoria: el producto es refrigerado'
          : fuera && l.estado_recepcion === 'CONFORME'
            ? `Fuera del rango del producto (${min ?? '—'} a ${max ?? '—'} °C): márcala Rechazado o En evaluación`
            : null
      if (!mensaje) return
      tempMal = true
      form.setError(`lineas.${i}.temperatura_recepcion`, { message: mensaje }, { shouldFocus: true })
    })
    if (tempMal) return
    try {
      // Inventario de destino de cada línea: el del producto en el rack elegido; si no existe, se crea vacío.
      const detalles: DetalleRecepcionCreate[] = []
      for (const l of v.lineas.filter((x) => x.incluir)) {
        const idProducto = pendientes.find((p) => p.detalle.id_detalle_reposicion === l.id_detalle_reposicion)!.detalle.id_producto
        const enRack = await qc.fetchQuery({
          queryKey: queryKeys.inventarios.byRack(l.id_rack),
          queryFn: () => inventariosApi.listByRack(l.id_rack),
          staleTime: 0,
        })
        const u = unidadesAUbicar(l)
        const inv =
          enRack.find((i) => i.id_producto === idProducto) ??
          (await crearInv.mutateAsync({
            id_producto: idProducto,
            id_rack: l.id_rack,
            stock_actual: 0,
            stock_minimo: l.stock_minimo.trim() === '' ? 0 : num(l.stock_minimo),
            stock_maximo: l.stock_maximo.trim() === '' ? Math.max(u, 1) : num(l.stock_maximo),
          }))
        detalles.push(aDetalleCreate(l, inv.id_inventario))
      }
      const rec = await crear.mutateAsync({
        id_orden_reposicion: orden.id_orden_reposicion,
        observaciones_generales: v.observaciones_generales,
        detalles,
      })
      const enEval = rec.detalles.filter((d) => d.estado_recepcion === 'EN_EVALUACION').length
      toast.success(
        enEval > 0 ? `Lo aceptado ya ingresó al inventario. ${enEval} línea(s) en evaluación por resolver.` : 'Lo aceptado ya ingresó al inventario.',
        'Recepción registrada',
      )
      onCreated(rec)
    } catch (e) {
      // 409 (kg / estado / temperatura del rack, sobre-recepción): refrescar racks y stock para volver a elegir.
      void qc.invalidateQueries({ queryKey: queryKeys.racks.all })
      void qc.invalidateQueries({ queryKey: queryKeys.inventarios.all })
      void qc.invalidateQueries({ queryKey: queryKeys.recepciones.all })
      apiError.handle(e, { form, titulo: 'No se pudo registrar la recepción' })
    }
  })

  return (
    <form id={FORM_ID} onSubmit={submit} noValidate className="flex flex-col gap-4">
      {orden.despacho ? (
        <FormAlert tone="info" title="Datos precargados del despacho del proveedor">
          Revisa cantidad, vencimiento y temperatura contra lo que llegó realmente.
          {orden.despacho.observacion ? ` Nota del proveedor: ${orden.despacho.observacion}` : ''}
        </FormAlert>
      ) : (
        <FormAlert tone="warning" title="El proveedor aún no registró su despacho">
          Puedes recibir igualmente: indica tú las cantidades.
        </FormAlert>
      )}
      <Field label="Observaciones generales" error={err.observaciones_generales?.message}>
        <Textarea rows={2} maxLength={1000} placeholder="Guía de remisión 001-2345, camión refrigerado" {...register('observaciones_generales')} />
      </Field>

      <fieldset className="flex flex-col gap-3">
        <legend className="mb-2 text-base font-semibold text-fg">Mercadería recibida</legend>
        {errorRaiz && (
          <p className="text-sm font-medium text-danger" role="alert">
            {errorRaiz}
          </p>
        )}
        {fields.map((f, i) => {
          const linea = pendientes[i]
          if (!linea) return null
          return (
            <LineaFila
              key={f.id}
              index={i}
              linea={linea}
              idAlmacen={orden.id_almacen}
              despachada={orden.despacho?.lineas.find((x) => x.id_detalle_reposicion === linea.detalle.id_detalle_reposicion)?.cantidad}
              nombreProducto={nombres.producto(linea.detalle.id_producto)}
              control={control}
              register={register}
              setValue={setValue}
              revalidarComentario={() => formState.isSubmitted && void trigger(`lineas.${i}.comentario_recepcion`)}
              errores={err.lineas?.[i]}
            />
          )
        })}
      </fieldset>

      <ApiErrorAlert error={apiError.error} />
    </form>
  )
}

function LineaFila({
  index,
  linea,
  idAlmacen,
  despachada,
  nombreProducto,
  control,
  register,
  setValue,
  revalidarComentario,
  errores,
}: {
  index: number
  linea: LineaPendiente
  idAlmacen: string
  /** Unidades que el proveedor dijo despachar (si registró su despacho). */
  despachada: number | undefined
  nombreProducto: string
  control: Control<In, unknown, Out>
  register: UseFormRegister<In>
  setValue: UseFormSetValue<In>
  /** El comentario depende del estado: revalidarlo al cambiar el estado. */
  revalidarComentario: () => void
  errores: FieldErrors<LineaIn> | undefined
}) {
  const productos = useProductos()
  const producto = productos.data?.find((p) => p.id_producto === linea.detalle.id_producto)
  const pref = `lineas.${index}` as const
  const [incluir, estado, recibidaTxt, rechazadaTxt, idRack] = useWatch({
    control,
    name: [`${pref}.incluir`, `${pref}.estado_recepcion`, `${pref}.cantidad_recibida`, `${pref}.cantidad_rechazada`, `${pref}.id_rack`],
  })
  const unidades = unidadesAUbicar({ cantidad_recibida: recibidaTxt, cantidad_rechazada: rechazadaTxt, estado_recepcion: estado })
  const hayRechazo = estado === 'CONFORME' && num(rechazadaTxt) > 0

  // Racks DISPONIBLES donde caben esas unidades del producto (kg y temperatura: lo decide el backend);
  // primero los que ya contienen el producto.
  const racksQ = useRacksDisponibles(incluir ? idAlmacen : undefined, linea.detalle.id_producto, unidades)
  const invsQ = useInventarios()
  const cargandoRacks = (racksQ.isLoading && !racksQ.data) || invsQ.isLoading
  const errorRacks = racksQ.data ? null : (racksQ.error ?? invsQ.error)
  const invEn = (idR: string) => (invsQ.data ?? []).find((i) => i.id_rack === idR && i.id_producto === linea.detalle.id_producto)
  const racks = [...(racksQ.data ?? [])].sort((a, b) => Number(!!invEn(b.id_rack)) - Number(!!invEn(a.id_rack)) || b.libre_kg - a.libre_kg)
  const kg = unidades * (producto?.peso ?? 0)
  const opcionesRack = racks.map((r) => {
    const inv = invEn(r.id_rack)
    const temp = temperaturaRack(r)
    return {
      value: r.id_rack,
      label: `${r.codigo} · ${r.nombre_zona ?? 'Zona'} · nivel ${r.nivel} · ${formatNumero(r.libre_kg)} kg libres${temp ? ` · ${temp}` : ''}${inv ? ` · ya tiene este producto (stock ${formatNumero(inv.stock_actual)})` : ''}`,
    }
  })
  const rackSel = racks.find((r) => r.id_rack === idRack)
  const crearInventario = !!rackSel && !invEn(rackSel.id_rack)
  // Si el rack elegido deja de tener espacio (cambió la cantidad o el stock), hay que volver a elegir.
  const rackPerdido = incluir && !!idRack && !cargandoRacks && !racksQ.isPlaceholderData && !rackSel
  useEffect(() => {
    if (rackPerdido) setValue(`${pref}.id_rack`, '')
  }, [rackPerdido, pref, setValue])

  return (
    <div className={cn('rounded-[var(--radius-ui)] border p-3', incluir ? 'border-accent/50 bg-surface' : 'border-border bg-surface-2/50')}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Controller
          control={control}
          name={`${pref}.incluir`}
          render={({ field }) => (
            <Checkbox
              label={<span className="font-semibold text-fg">{nombreProducto}</span>}
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
              onBlur={field.onBlur}
              ref={field.ref}
            />
          )}
        />
        <span className="font-mono text-xs text-fg-muted tabular">
          Pendiente {formatNumero(linea.pendiente)} de {formatNumero(linea.solicitada)}
          {despachada !== undefined && ` · despachadas ${formatNumero(despachada)}`}
        </span>
      </div>

      {incluir && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Cantidad recibida" error={errores?.cantidad_recibida?.message} required>
            <Input size="lg" type="number" inputMode="numeric" min={1} step={1} suffix="u." {...register(`${pref}.cantidad_recibida`)} />
          </Field>
          {estado === 'CONFORME' && (
            <Field label="Rechazadas" error={errores?.cantidad_rechazada?.message} hint="Unidades que no se aceptan.">
              <Input
                size="lg"
                type="number"
                inputMode="numeric"
                min={0}
                step={1}
                suffix="u."
                {...register(`${pref}.cantidad_rechazada`, { onChange: revalidarComentario })}
              />
            </Field>
          )}
          <Field label="Estado" error={errores?.estado_recepcion?.message} required>
            <Select size="lg" options={ESTADO_RECEPCION_OPCIONES} placeholder={false} {...register(`${pref}.estado_recepcion`, { onChange: revalidarComentario })} />
          </Field>
          <Field label="Vencimiento" error={errores?.fecha_vencimiento?.message} hint="Opcional.">
            <Input size="lg" type="date" {...register(`${pref}.fecha_vencimiento`)} />
          </Field>
          <Field
            label="Temperatura"
            error={errores?.temperatura_recepcion?.message}
            required={!!producto?.requiere_refrigeracion}
            hint={
              producto?.requiere_refrigeracion
                ? `Debe estar entre ${producto.temperatura_min_almacenamiento ?? '—'} y ${producto.temperatura_max_almacenamiento ?? '—'} °C.`
                : 'Opcional.'
            }
          >
            <Input size="lg" type="number" inputMode="decimal" step="any" suffix="°C" {...register(`${pref}.temperatura_recepcion`)} />
          </Field>
          <Field
            label="Comentario"
            error={errores?.comentario_recepcion?.message}
            required={estado !== 'CONFORME' || hayRechazo}
            hint={estado === 'CONFORME' && !hayRechazo ? 'Opcional.' : 'Motivo del rechazo o de la evaluación.'}
          >
            <Input size="lg" maxLength={1000} placeholder={estado === 'CONFORME' ? '' : 'Cajas golpeadas'} {...register(`${pref}.comentario_recepcion`)} />
          </Field>
          <Field
            label="Guardar en el rack"
            error={errores?.id_rack?.message}
            required
            className="sm:col-span-2 lg:col-span-3"
            hint={
              estado === 'RECHAZADO'
                ? 'Mercadería rechazada: no ingresa stock, pero el registro necesita una ubicación de referencia.'
                : estado === 'EN_EVALUACION'
                  ? `Ingresará aquí cuando se resuelva la evaluación (${formatNumero(unidades)} u.).`
                  : `Racks libres que soportan ${formatNumero(kg)} kg (${formatNumero(unidades)} u.)${producto?.requiere_refrigeracion ? ' y cumplen su temperatura' : ''}.`
            }
          >
            {cargandoRacks ? (
              <Select size="lg" disabled placeholder="Buscando racks con espacio…" />
            ) : errorRacks ? (
              <Select size="lg" disabled placeholder={errorRacks instanceof ApiError ? `Error: ${errorRacks.detail}` : 'Error al cargar los racks'} />
            ) : opcionesRack.length === 0 ? (
              <Select size="lg" disabled placeholder={`Ningún rack libre soporta ${formatNumero(kg)} kg${producto?.requiere_refrigeracion ? ' con la temperatura del producto' : ''}`} />
            ) : (
              <Controller
                control={control}
                name={`${pref}.id_rack`}
                render={({ field }) => (
                  <Select
                    size="lg"
                    options={opcionesRack}
                    placeholder="Elige un rack…"
                    name={field.name}
                    ref={field.ref}
                    value={field.value}
                    onBlur={field.onBlur}
                    onChange={(e) => {
                      field.onChange(e.target.value)
                      const s = sugerirMinMax(Math.max(unidades, 1))
                      setValue(`${pref}.stock_minimo`, s.minimo)
                      setValue(`${pref}.stock_maximo`, s.maximo)
                    }}
                  />
                )}
              />
            )}
          </Field>
          {crearInventario && (
            <>
              <p className="flex items-start gap-2 text-sm text-fg-muted sm:col-span-2 lg:col-span-1">
                El producto aún no está en el rack {rackSel?.codigo}: se creará su inventario (stock inicial 0).
              </p>
              <Field label="Stock mínimo" error={errores?.stock_minimo?.message}>
                <Input type="number" inputMode="numeric" min={0} step={1} suffix="u." {...register(`${pref}.stock_minimo`)} />
              </Field>
              <Field label="Stock máximo" error={errores?.stock_maximo?.message}>
                <Input type="number" inputMode="numeric" min={0} step={1} suffix="u." {...register(`${pref}.stock_maximo`)} />
              </Field>
            </>
          )}
        </div>
      )}
    </div>
  )
}
