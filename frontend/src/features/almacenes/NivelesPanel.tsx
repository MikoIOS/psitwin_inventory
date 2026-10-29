import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { abastecimientoApi } from '@/api/abastecimiento'
import { ApiError } from '@/api/client'
import { useRol } from '@/auth/useRol'
import { Button, Field, Input, Select } from '@/components/ui'
import type { Rack } from '@/api/types'
import { api } from '@/api/client'

export function NivelesPanel({ rack }: { rack: Rack }) {
  const query = useQuery({ queryKey: ['niveles', rack.id_rack], queryFn: () => abastecimientoApi.niveles(rack.id_rack) })
  const qc = useQueryClient()
  const { esEmpresa } = useRol()
  const [code, setCode] = useState('')
  const [number, setNumber] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const available = Array.from({ length: rack.max_niveles ?? 1 }, (_, i) => i + 1).filter(n => !query.data?.some(level => level.numero === n))
  const selected = available.includes(Number(number)) ? number : String(available[0] ?? '')
  const perform = async (action: () => Promise<unknown>) => {
    setBusy(true); setError('')
    try { await action(); setCode(''); await query.refetch(); await qc.invalidateQueries({ queryKey: ['plano'] }) }
    catch (cause) { setError(cause instanceof ApiError ? cause.detail : 'No se pudo actualizar los niveles.') }
    finally { setBusy(false) }
  }
  return <section className="mb-4 space-y-3 rounded-lg border border-border p-3" aria-label="Niveles del rack">
    <h3 className="font-semibold">Niveles del rack ({query.data?.length ?? 0}/{rack.max_niveles ?? 1})</h3>
    {query.isError ? <p role="alert">No se pudo consultar los niveles.</p> : query.isPending ? <p role="status">Consultando niveles…</p> : !query.data?.length ? <p className="text-sm">No hay niveles registrados.</p> : <ul className="space-y-2">{query.data.map(level => <li key={level.id_nivel} className="flex items-center justify-between text-sm">Nivel {level.numero} · {level.codigo}{esEmpresa && <Button size="sm" variant="ghost" disabled={busy} onClick={() => void perform(() => abastecimientoApi.eliminarNivel(level.id_nivel))}>Eliminar nivel</Button>}</li>)}</ul>}
    {esEmpresa && query.data?.map(level => <div key={'estado-' + level.id_nivel} className="flex flex-wrap items-center gap-2 text-sm">
      <span>Nivel {level.numero}</span>
      <Button size="sm" variant="ghost" disabled={busy} onClick={() => void perform(() => api.patch('/abastecimiento/niveles/' + encodeURIComponent(level.id_nivel), {estado:'INACTIVO'}))}>Desactivar</Button>
      <Button size="sm" variant="ghost" disabled={busy} onClick={() => void perform(() => api.patch('/abastecimiento/niveles/' + encodeURIComponent(level.id_nivel), {estado:'ARCHIVADO'}))}>Archivar</Button>
      <Button size="sm" variant="ghost" disabled={busy} onClick={() => void perform(() => api.patch('/abastecimiento/niveles/' + encodeURIComponent(level.id_nivel), {estado:'ACTIVO'}))}>Activar</Button>
    </div>)}
    {esEmpresa && <form onSubmit={event => { event.preventDefault(); void perform(() => abastecimientoApi.crearNivel(rack.id_rack, { codigo: code, numero: Number(selected) })) }} className="space-y-2">
      <Field label="Código del nivel"><Input value={code} onChange={e => setCode(e.target.value)} maxLength={50} required disabled={!available.length || busy} /></Field>
      <Field label="Número del nivel"><Select value={selected} onChange={e => setNumber(e.target.value)} placeholder={false} options={available.map(n => ({ value: String(n), label: `Nivel ${n}` }))} disabled={!available.length || busy} /></Field>
      <Button type="submit" size="sm" disabled={!code.trim() || !available.length || busy || query.isError}>Agregar nivel</Button>
    </form>}
    {error && <p role="alert" className="text-sm text-danger">{error}</p>}
  </section>
}
