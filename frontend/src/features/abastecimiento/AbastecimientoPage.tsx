import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router'
import { abastecimientoApi, useOfertas } from '@/api/abastecimiento'
import { ApiError } from '@/api/client'
import { useSession } from '@/auth/SessionContext'
import { Button, Card, Field, Input, Select, Textarea, Modal, LinkButton } from '@/components/ui'
import { formatMoneda, formatFechaHora } from '@/lib/format'
import { paths } from '@/paths'
import { OrdenCrearModal } from '@/features/ordenes/OrdenForm'
import { PedidosHistoryPanel } from './PedidosHistoryPanel'

export default function AbastecimientoPage() {
  const { rol } = useSession()
  const supplier = rol === 'PROVEEDOR'
  const [search] = useSearchParams()
  const [tab, setTab] = useState<'seguimiento' | 'ofertas' | 'historial'>(supplier && search.get('producto') ? 'ofertas' : 'seguimiento')
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()
  const offers = useOfertas(!supplier)
  const tracking = useQuery({ queryKey: ['abastecimiento', 'seguimiento'], queryFn: abastecimientoApi.seguimiento })
  const catalog = useQuery({ queryKey: ['abastecimiento', 'catalogo'], queryFn: abastecimientoApi.catalogo })
  const names = new Map(catalog.data?.map(p => [p.id_producto, p.nombre]))
  const [decision, setDecision] = useState<{ id: string; kind: 'MANTENER' | 'CERRAR' | 'RECHAZAR' } | null>(null)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const resolve = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!decision || !reason.trim()) return
    setBusy(true); setError('')
    try {
      if (decision.kind === 'RECHAZAR') await abastecimientoApi.rechazar(decision.id, reason.trim())
      else await abastecimientoApi.decidir(decision.id, decision.kind, reason.trim())
      setDecision(null); setReason(''); void tracking.refetch(); void offers.refetch()
    } catch (cause) { setError(cause instanceof ApiError ? cause.detail : 'No se pudo registrar la decisión.') }
    finally { setBusy(false) }
  }
  return <div className="space-y-6">
    <header className="flex flex-wrap justify-between gap-3"><div><h1 className="text-2xl font-semibold">Abastecimiento</h1><p className="text-sm text-fg-muted">Ofertas, solicitudes, despachos y cantidades realmente aceptadas.</p></div>{rol === 'OPERARIO' && <Button onClick={() => setCreating(true)}>Nueva solicitud</Button>}</header>
    <nav aria-label="Vistas de abastecimiento" className="flex flex-wrap gap-2">
      <Button variant={tab === 'seguimiento' ? 'primary' : 'secondary'} onClick={() => setTab('seguimiento')}>{supplier ? 'Solicitudes y despachos' : 'Seguimiento y faltantes'}</Button>
      <Button variant={tab === 'ofertas' ? 'primary' : 'secondary'} onClick={() => setTab('ofertas')}>{supplier ? 'Configurar ofertas' : 'Ofertas disponibles'}</Button>
      {!supplier && <Button variant={tab === 'historial' ? 'primary' : 'secondary'} onClick={() => setTab('historial')}>Historial de pedidos</Button>}
    </nav>
    {tab === 'ofertas' && <>
      {supplier && <OfertaEditor />}
      <Card title={supplier ? 'Mis ofertas' : 'Ofertas disponibles'}>
        {offers.isError ? <p role="alert">No se pudieron consultar las ofertas. <Button onClick={() => void offers.refetch()}>Reintentar</Button></p> : offers.isPending ? <p role="status">Consultando ofertas…</p> : !offers.data?.length ? <p>No hay ofertas disponibles.</p> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Proveedor', 'Producto', 'Clasificación', 'Precio PEN', 'Total ofertado', 'Reservado', 'Despachado', 'Disponible'].map(c => <th className="p-2" key={c}>{c}</th>)}</tr></thead><tbody>{offers.data.map(o => <tr key={o.id_oferta} className="border-t border-border"><td className="p-2">{o.proveedor}</td><td className="p-2">{o.producto}</td><td className="p-2">{o.familia} / {o.categoria}</td><td className="p-2">{formatMoneda(o.precio_centimos / 100)}/{o.unidad}</td><td className="p-2">{o.cantidad_total} {o.unidad}</td><td className="p-2">{o.cantidad_reservada}</td><td className="p-2">{o.cantidad_despachada}</td><td className="p-2">{o.activa ? o.cantidad_disponible : 'Inactiva'}</td></tr>)}</tbody></table></div>}
      </Card>
    </>}
    {tab === 'seguimiento' && <Card title={supplier ? 'Solicitudes recibidas' : 'Solicitado, despachado y recibido'}>
      {tracking.isError ? <p role="alert">No se pudo consultar el seguimiento. <Button onClick={() => void tracking.refetch()}>Reintentar</Button></p> : tracking.isPending ? <p role="status">Consultando solicitudes…</p> : !tracking.data?.length ? <p>No hay solicitudes registradas para tu sesión.</p> : <div className="space-y-4">{tracking.data.map((row, index) => <article key={`${row.id_orden}:${row.id_producto}:${index}`} className="rounded-xl border border-border p-4">
        <div className="flex flex-wrap justify-between gap-2"><p className="font-semibold">{names.get(row.id_producto) ?? row.id_producto} · {row.proveedor}</p><span>{row.estado} · {formatFechaHora(row.fecha)}</span></div>
        <p className="my-2 text-sm">Solicitado: {row.solicitada} · Despachado: {row.despachada} · Recibido: {row.recibida} · Aceptado: {row.aceptada} · Rechazado: {row.rechazada} · Faltante por aceptar: {row.faltante} {row.unidad ?? 'unidad'}</p>
        <p className="text-sm text-fg-muted">Diferencia respecto al despacho: {row.diferencia_despacho} {row.unidad ?? 'unidad'}</p>
        {row.motivos.filter(Boolean).map((m, i) => <p className="mt-2 text-sm" key={i}>Motivo registrado: {m}</p>)}
        {row.resolucion && <p className="my-2 text-sm">Resolución: {row.resolucion.decision} · {row.resolucion.motivo}</p>}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <LinkButton size="sm" to={paths.orden(row.id_orden)}>{supplier ? 'Revisar y registrar despacho' : rol === 'OPERARIO' ? 'Revisar solicitud y recepción' : 'Ver solicitud y decisiones'}</LinkButton>
          {rol === 'EMPRESA' && <>
            <Contacto telefono={row.telefono} />
            {['PENDIENTE', 'OBSERVADA'].includes(row.estado) && <Button size="sm" variant="secondary" onClick={() => { setDecision({ id: row.id_orden, kind: 'RECHAZAR' }); setReason(''); setError('') }}>Rechazar solicitud</Button>}
            {row.faltante > 0 && ['ENVIADA', 'PARCIAL'].includes(row.estado) && <><Button size="sm" variant="secondary" onClick={() => { setDecision({ id: row.id_orden, kind: 'MANTENER' }); setReason(''); setError('') }}>Mantener pendiente</Button><Button size="sm" variant="ghost" onClick={() => { setDecision({ id: row.id_orden, kind: 'CERRAR' }); setReason(''); setError('') }}>Cerrar pendiente</Button></>}
          </>}
        </div>
      </article>)}</div>}
    </Card>}
    {tab === 'historial' && !supplier && <PedidosHistoryPanel />}
    <OrdenCrearModal open={creating} onClose={() => setCreating(false)} onCreated={order => { setCreating(false); navigate(paths.orden(order.id_orden_reposicion)) }} />
    <Modal open={!!decision} onClose={() => setDecision(null)} title="Confirmar decisión de la empresa">
      <form onSubmit={resolve} className="space-y-4"><p>{decision?.kind === 'RECHAZAR' ? 'Rechazar solicitud y liberar reservas.' : decision?.kind === 'CERRAR' ? 'Cerrar el pendiente conservando el historial.' : 'Mantener el faltante vinculado a la solicitud, sin crear otra compra.'}</p><Field label="Motivo" required><Textarea value={reason} onChange={e => setReason(e.target.value)} maxLength={1000} required /></Field>{error && <p role="alert">{error}</p>}<Button type="submit" loading={busy} disabled={!reason.trim()}>Confirmar decisión</Button></form>
    </Modal>
  </div>
}

function Contacto({ telefono }: { telefono: string | null }) {
  const digits = (telefono ?? '').replace(/\D/g, '')
  if (!/^\d{7,15}$/.test(digits)) return <span className="text-sm text-fg-muted">Teléfono no registrado</span>
  return <><a href={`tel:${digits}`} className="text-sm text-blue-400">{telefono}</a><Button size="sm" variant="ghost" onClick={() => { void navigator.clipboard.writeText(telefono ?? '') }}>Copiar teléfono</Button></>
}

function OfertaEditor() {
  const [search] = useSearchParams()
  const catalog = useQuery({ queryKey: ['abastecimiento', 'catalogo'], queryFn: abastecimientoApi.catalogo })
  const offers = useOfertas()
  const queryClient = useQueryClient()
  const [product, setProduct] = useState(search.get('producto') ?? '')
  const [price, setPrice] = useState('')
  const [total, setTotal] = useState('')
  const [active, setActive] = useState(true)
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const selected = catalog.data?.find(p => p.id_producto === product)
  const unit = selected?.unidad ?? 'unidad'
  const choose = (id: string) => { setProduct(id); const offer = offers.data?.find(o => o.id_producto === id); setPrice(offer ? String(offer.precio_centimos / 100) : ''); setTotal(offer ? String(offer.cantidad_total) : ''); setActive(offer?.activa ?? true); setNotes(offer?.observaciones ?? '') }
  const save = async (event: React.FormEvent) => {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      await abastecimientoApi.guardarOferta({ id_producto: product, unidad: unit, precio: price, cantidad_total: Number(total), activa: active, observaciones: notes })
      await queryClient.invalidateQueries({ queryKey: ['abastecimiento', 'ofertas'] })
    } catch (cause) { setError(cause instanceof ApiError ? cause.detail : 'No se pudo guardar la oferta.') }
    finally { setBusy(false) }
  }
  return <Card title="Configurar oferta" description="El producto pertenece al catálogo; su disponibilidad externa no es stock del almacén.">
    {catalog.isError ? <p role="alert">No se pudo cargar el catálogo.</p> : <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
      <Field label="Producto del catálogo" required><Select value={product} onChange={e => choose(e.target.value)} options={(catalog.data ?? []).map(p => ({ value: p.id_producto, label: `${p.nombre} · ${p.familia} / ${p.categoria}` }))} /></Field>
      <Field label={`Precio por ${unit} (PEN)`} required><Input type="number" min=".01" step=".01" value={price} onChange={e => setPrice(e.target.value)} required /></Field>
      <Field label={`Cantidad total ofertada (${unit})`} required hint="Incluye lo reservado y despachado; la disponibilidad nueva se calcula descontándolos."><Input type="number" min={0} step={unit === 'kg' ? '.001' : '1'} value={total} onChange={e => setTotal(e.target.value)} required /></Field>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} />Oferta activa</label>
      <Field label="Observaciones"><Textarea value={notes} onChange={e => setNotes(e.target.value)} maxLength={1000} /></Field>
      {error && <p role="alert" className="text-danger">{error}</p>}
      <div className="flex flex-wrap gap-2 sm:col-span-2"><Button type="submit" loading={busy} disabled={!product}>Guardar oferta</Button><LinkButton variant="secondary" to={paths.productos}>Registrar un producto nuevo en el catálogo</LinkButton></div>
    </form>}
  </Card>
}
