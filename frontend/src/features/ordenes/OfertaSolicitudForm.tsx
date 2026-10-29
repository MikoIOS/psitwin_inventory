import { useState } from 'react'
import { useOfertas } from '@/api/abastecimiento'
import { useCreateOrden } from '@/api/ordenesReposicion'
import type { OrdenReposicion } from '@/api/types'
import { ApiError } from '@/api/client'
import { Button, Field, Input, Select, Textarea } from '@/components/ui'
import { formatMoneda } from '@/lib/format'
import { subtotalCentimos } from '@/lib/abastecimiento'

export function OfertaSolicitudForm({ crear, idProveedor, onCreated }: {
  crear: ReturnType<typeof useCreateOrden>; idProveedor: string | undefined; onCreated: (order: OrdenReposicion) => void
}) {
  const offers = useOfertas(true)
  const [provider, setProvider] = useState(idProveedor ?? '')
  const [quantities, setQuantities] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [key, setKey] = useState(() => crypto.randomUUID())
  const [error, setError] = useState('')
  const providers = [...new Map((offers.data ?? []).map(o => [o.id_proveedor, { value: o.id_proveedor, label: o.proveedor }])).values()]
  const rows = (offers.data ?? []).filter(o => o.id_proveedor === provider)
  const selected = rows.filter(o => Number((quantities[o.id_oferta] ?? '').replace(',', '.')) > 0)
  const invalid = selected.some(o => {
    const value = quantities[o.id_oferta] ?? ''
    const number = Number(value.replace(',', '.'))
    return subtotalCentimos(value, o.precio_centimos) === null || number > o.cantidad_disponible || (o.unidad === 'unidad' && !Number.isInteger(number))
  })
  const total = selected.reduce((sum, o) => sum + (subtotalCentimos(quantities[o.id_oferta]!, o.precio_centimos) ?? 0), 0)
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('')
    if (!selected.length || invalid) { setError('Selecciona cantidades válidas dentro de la disponibilidad del proveedor.'); return }
    if (!confirmed) { setConfirmed(true); return }
    try {
      const order = await crear.mutateAsync({ id_proveedor: provider, origen: 'MANUAL', observacion: notes || null,
        fecha_estimada_recepcion: null, clave_idempotencia: key,
        lineas: selected.map(o => ({ id_producto: o.id_producto, id_oferta: o.id_oferta,
          cantidad_solicitada: Number(quantities[o.id_oferta]!.replace(',', '.')), costo_unitario: null })) })
      onCreated(order)
    } catch (cause) { setError(cause instanceof ApiError ? cause.detail : 'No se pudo confirmar la solicitud.'); setConfirmed(false); void offers.refetch() }
  }
  return <form id="form-orden-crear" onSubmit={submit} className="space-y-4">
    {error && <p role="alert" className="text-danger">{error}</p>}
    {offers.isError ? <p role="alert">No se pudo consultar las ofertas. <Button onClick={() => void offers.refetch()}>Reintentar</Button></p> : offers.isPending ? <p role="status">Consultando ofertas…</p> : !offers.data?.length ? <p>No hay ofertas disponibles para solicitar.</p> : <>
      <Field label="Proveedor" required><Select disabled={confirmed} value={provider} onChange={e => { setProvider(e.target.value); setQuantities({}); setKey(crypto.randomUUID()) }} options={providers} /></Field>
      {rows.map(offer => <div key={offer.id_oferta} className="rounded-lg border border-border p-3">
        <p className="font-semibold">{offer.producto}</p><p className="text-sm text-fg-muted">{offer.familia} / {offer.categoria} · {formatMoneda(offer.precio_centimos / 100)}/{offer.unidad} · Disponible: {offer.cantidad_disponible} {offer.unidad}</p>
        <Field label={`Cantidad de ${offer.producto} (${offer.unidad})`}><Input type="number" min={0} max={offer.cantidad_disponible} step={offer.unidad === 'kg' ? '.001' : '1'} disabled={confirmed} value={quantities[offer.id_oferta] ?? ''} onChange={e => { setQuantities(values => ({ ...values, [offer.id_oferta]: e.target.value })); setKey(crypto.randomUUID()) }} /></Field>
        <p className="text-sm">Subtotal: {formatMoneda((subtotalCentimos(quantities[offer.id_oferta] || '0', offer.precio_centimos) ?? 0) / 100)}</p>
      </div>)}
      <Field label="Observaciones"><Textarea disabled={confirmed} value={notes} onChange={e => { setNotes(e.target.value); setKey(crypto.randomUUID()) }} maxLength={500} /></Field>
      <p className="font-semibold">Total estimado: {formatMoneda(total / 100)} PEN</p>
      {confirmed && <div role="status" className="rounded-lg border border-border p-3"><p>Resumen: {providers.find(p => p.value === provider)?.label} · {selected.length} productos · {formatMoneda(total / 100)} PEN.</p><p>Confirma para enviar a aprobación de la empresa.</p><Button variant="ghost" onClick={() => setConfirmed(false)}>Volver a editar</Button></div>}
      <Button type="submit" loading={crear.isPending} disabled={!selected.length || invalid}>{confirmed ? 'Confirmar solicitud' : 'Revisar solicitud'}</Button>
    </>}
  </form>
}
