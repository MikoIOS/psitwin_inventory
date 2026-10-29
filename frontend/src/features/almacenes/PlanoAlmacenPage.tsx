import { useMovimientosPorRack } from '@/api/movimientos'
import { ValoresVivos } from '@/features/monitoreo/ValoresVivos'
import { useAhora } from '@/features/monitoreo/monitoreoUtils'
import { WarehouseMap } from './WarehouseMap'
import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { usePlano } from '@/api/inventarioConsultas'
import { inventarioConsultasApi } from '@/api/inventarioConsultas'
import { useMutation } from '@tanstack/react-query'
import { useRol } from '@/auth/useRol'
import { Button, Card, PageHeader, LinkButton } from '@/components/ui'
import { useSaikiSessionOptional } from '@/features/saiki/SaikiSession'
import { paths } from '@/paths'

export default function PlanoAlmacenPage() {
  const { idAlmacen = '' } = useParams()
  const query = usePlano(idAlmacen)
  const { esEmpresa } = useRol()
  const enableLevels = useMutation({ mutationFn: inventarioConsultasApi.habilitar, onSuccess: () => { void query.refetch() } })
  const [params] = useSearchParams()
  const [zone, setZone] = useState(params.get('zona') ?? ''), [rack, setRack] = useState(params.get('rack') ?? ''), [level, setLevel] = useState(params.get('nivel') ?? '')
  const movements = useMovimientosPorRack(rack || undefined)
  const now = useAhora(2000)
  const session = useSaikiSessionOptional()
  const setContext = session?.setInventoryContext
  useEffect(() => { setContext?.({ id_almacen: idAlmacen, ...(zone ? { id_zona: zone } : {}), ...(rack ? { id_rack: rack } : {}), ...(level ? { id_nivel: level } : {}) }) }, [idAlmacen,zone,rack,level,setContext])
  const data = query.data
  if (query.isPending) return <p role="status">Cargando plano del almacén…</p>
  if (query.isError || !data) return <p role="alert">No se pudo consultar el plano. <Button onClick={() => void query.refetch()}>Reintentar</Button></p>
  const selected = data.racks.find(r => r.id_rack === rack)
  const levels = data.niveles.filter(n => n.id_rack === rack).sort((a,b) => b.numero-a.numero)
  const rows = data.inventario.filter(i => (!zone || i.id_zona === zone) && (!rack || i.id_rack === rack) && (!level || i.id_nivel === level))
  const alerts = data.alertas.filter(a => a.id_detalle_inventario
    ? rows.some(r => r.id_detalle_inventario === a.id_detalle_inventario)
    : (!zone || a.id_zona === zone) && (!rack || a.id_rack === rack) && (!level || a.id_nivel === level))
  return <div className="space-y-5">
    <PageHeader title="Plano del almacén" description={`${data.almacen.nombre} · Esquema organizado, sin escala física.`} back={{ to: paths.almacen(idAlmacen), label: 'Almacén' }} />
    <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => { setZone(''); setRack(''); setLevel('') }}>Ver todo el almacén</Button><Button variant="ghost" onClick={() => void query.refetch()}>Actualizar plano</Button><LinkButton to={paths.saiki}>Preguntar a Saiki sobre esta ubicación</LinkButton></div>
    <WarehouseMap data={data} onSelect={(z,r,n) => { setZone(z); setRack(r); setLevel(n) }} />
    {selected && <div className="flex flex-wrap gap-2">
      <LinkButton to={paths.zona(idAlmacen, selected.id_zona)}>Configurar rack y tipo</LinkButton>
      {esEmpresa && levels.length !== selected.max_niveles && <Button loading={enableLevels.isPending} onClick={() => enableLevels.mutate(selected.id_rack)}>Habilitar niveles configurados</Button>}
      {enableLevels.isError && <p role="alert">No se pudieron habilitar los niveles.</p>}
    </div>}
    <Card title="Inventario de la ubicación seleccionada">
      <p className="mb-3 text-sm text-fg-muted">{data.almacen.nombre} / {data.zonas.find(z => (z.id_zona ?? z.id) === zone)?.nombre ?? 'Todas las zonas'} / {selected?.codigo ?? 'Todos los racks'} / {levels.find(n => n.id_nivel === level)?.codigo ?? 'Todos los niveles'}</p>
      {!rows.length ? <p>No hay inventario registrado en esta ubicación.</p> : <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Producto','Cantidad','Unidad','Nivel','Estado'].map(h => <th key={h} className="p-2">{h}</th>)}</tr></thead><tbody>{rows.map(r => <tr key={r.id_detalle_inventario} className="border-t border-border"><td className="p-2">{r.producto}</td><td className="p-2">{r.stock_actual}</td><td className="p-2">{r.unidad}</td><td className="p-2">{r.nivel ?? 'Sin nivel asignado'}</td><td className="p-2">{r.estado}</td></tr>)}</tbody></table></div>}
      <p className="mt-3 text-xs text-fg-muted">Actualización automática cada 5 segundos. Última consulta: {new Date(data.generado_en).toLocaleString('es-PE')}</p>
      <h3 className="mt-4 font-semibold">Alertas asociadas</h3>{alerts.length ? alerts.map((a,i) => <p key={i} className="mt-2 text-sm text-amber-200">{a.producto ?? 'Ubicación/equipo'}: {a.tipo} · {a.observacion}</p>) : <p className="mt-2 text-sm">Sin alertas registradas para este alcance.</p>}
      {level && <>
        <h3 className="mt-4 font-semibold">Sensores del nivel</h3>
        {data.niveles.find(n => n.id_nivel === level)?.sensores?.map(d => <div key={d.id_dispositivo} className="my-3"><p>{d.nombre}</p><ValoresVivos dispositivo={d} estado={d.estado} rack={undefined} ahora={now} /></div>)}
        <h3 className="mt-4 font-semibold">Movimientos del nivel</h3>
        {movements.isError ? <p role="alert">No se pudieron consultar los movimientos.</p> : movements.data?.filter(m => m.id_nivel === level).slice(0,30).map(m => <p key={m.id_movimiento}>{m.fecha_hora} · {m.tipo_movimiento} · {m.cantidad}</p>)}
      </>}
    </Card>
  </div>
}
