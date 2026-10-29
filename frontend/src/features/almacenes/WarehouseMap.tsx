import { memo, useState } from 'react'
import type { Plano } from '@/api/inventarioConsultas'
import { usePlano } from '@/api/inventarioConsultas'
import { useAlmacenes } from '@/api/almacenes'
import { useMonitoreoVivo } from '@/api/monitoreo'
import { useAhora, estadoDispositivo } from '@/features/monitoreo/monitoreoUtils'
import { LinkButton } from '@/components/ui'
import { paths } from '@/paths'
import { useNavigate } from 'react-router'
import { useRol } from '@/auth/useRol'

export const COLORES_NIVEL: Record<string, string> = {
  critico: 'bg-red-100 text-red-950 border-red-600', advertencia: 'bg-amber-100 text-amber-950 border-amber-600',
  normal: 'bg-green-100 text-green-950 border-green-600', sin_datos: 'bg-slate-100 text-slate-950 border-slate-500',
  desconectado: 'bg-violet-100 text-violet-950 border-violet-600 border-dashed',
}
export function productosNivel(data: Plano, id: string) {
  return [...new Set(data.inventario.filter(i => i.id_nivel === id && i.stock_actual > 0 && i.ubicacion_valida && !i.rechazado).map(i => i.producto))].sort((a,b) => a.localeCompare(b,'es'))
}
const activo = (r: { estado?: string }) => !['INACTIVO','DESACTIVADO','ARCHIVADO'].includes(r.estado ?? '')
export const WarehouseMap = memo(function WarehouseMap({ data, onSelect }: { data: Plano; onSelect?: (zona: string, rack: string, nivel: string) => void }) {
  const [filter, setFilter] = useState('activos')
  return <section aria-label="Contorno del almacén" className="my-5 rounded-xl border p-4">
    <h2 className="font-semibold">Plano de {data.almacen.nombre}</h2>
    <label>Ubicaciones <select value={filter} onChange={e => setFilter(e.target.value)}><option value="activos">Activas</option><option value="todos">Todas, incluido historial</option></select></label>
    <p className="my-2 text-sm">Rojo: crítica · Ámbar: advertencia · Verde: normal reciente · Gris: sin datos · Violeta discontinuo: desconectado</p>
    <div className="grid gap-4 lg:grid-cols-2">{data.zonas.filter(z => filter === 'todos' || activo(z)).map(z => {
      const zid = z.id_zona ?? z.id
      return <section key={zid} className="rounded-xl border p-3"><h3 className="font-semibold">{z.nombre}{!activo(z) && <small> · {z.estado}</small>}</h3>
        <div className="grid gap-3 sm:grid-cols-2">{data.racks.filter(r => r.id_zona === zid && (filter === 'todos' || activo(r))).map(r => {
          const levels = data.niveles.filter(n => n.id_rack === r.id_rack && (filter === 'todos' || activo(n))).sort((a,b) => b.numero-a.numero)
          return <section key={r.id_rack} className="min-w-0 rounded-lg border p-3"><h4 className="font-semibold"><button onClick={() => onSelect?.(zid,r.id_rack,'')}>Rack {r.codigo} — {r.tipo_rack || 'Tipo no definido'}</button></h4><p className="text-sm">{levels.length} niveles{!activo(r) && ' · ' + r.estado}</p>
            <div className="mt-2 space-y-2">{levels.map(n => {
              const names = productosNivel(data,n.id_nivel)
              return <WarehouseLevel key={n.id_nivel} n={n} names={names} onSelect={() => onSelect?.(zid,r.id_rack,n.id_nivel)} />
            })}</div>
          </section>
        })}</div>
      </section>
    })}</div>
  </section>
})
export function WarehouseMapSelector() {
  const warehouses = useAlmacenes()
  const navigate = useNavigate()
  const { esOperario, idAlmacen } = useRol()
  const [selected,setSelected] = useState('')
  const available = (warehouses.data ?? []).filter(w => !esOperario || w.id_almacen === idAlmacen)
  const id = available.some(w => w.id_almacen === selected) ? selected : available[0]?.id_almacen ?? ''
  const query = usePlano(id)
  return <section className="my-5"><label>Almacén del plano <select value={id} onChange={e => setSelected(e.target.value)}>{available.map(w => <option key={w.id_almacen} value={w.id_almacen}>{w.nombre}</option>)}</select></label>
    {query.data && <><WarehouseMap data={query.data} onSelect={(zona,rack,nivel) => navigate(paths.plano(id) + '?' + new URLSearchParams({zona,rack,nivel}))} /><LinkButton to={paths.plano(id)}>Ver detalle de niveles</LinkButton></>}
    {query.isError && <p role="alert">No se pudo actualizar el plano.</p>}
  </section>
}

const WarehouseLevel = memo(function WarehouseLevel({n,names,onSelect}: {n: Plano['niveles'][number]; names: string[]; onSelect: () => void}) {
  const live = useMonitoreoVivo()
  const now = useAhora(2000)
              const devices = n.sensores ?? []
              let status = n.monitoreo ?? 'sin_datos'
              if (devices.length) {
                const states: string[] = devices.map(d => {
                  const state = live?.dispositivos.get(d.id_dispositivo)?.estado ?? d.estado
                  if (state?.alertas_abiertas.length) return state.alertas_abiertas.some(a => /CRITIC|ALT[OA]/.test(a.nivel_riesgo ?? '')) ? 'critico' : 'advertencia'
                  if (!state?.conectado) return 'desconectado'
                  const result = estadoDispositivo(d,state,now)
                  return result === 'normal' ? 'normal' : result === 'fuera' ? 'advertencia' : 'sin_datos'
                })
                status = ['critico','advertencia','desconectado','sin_datos','normal'].find(s => states.includes(s)) ?? 'sin_datos'
              }
              return <div key={n.id_nivel} data-nivel={n.id_nivel} data-estado={status} className={'rounded border-b-4 p-2 ' + (COLORES_NIVEL[status] ?? COLORES_NIVEL.sin_datos)}>
                <button className="w-full text-left" onClick={() => onSelect()}><strong>Nivel {n.numero}{!activo(n) && ' · ' + n.estado}</strong><span className="block break-words">{names.slice(0,3).join(', ') || 'Vacío'}</span></button>
                {names.length > 3 && <details><summary>+{names.length-3} productos</summary><p className="break-words">{names.slice(3).join(', ')}</p></details>}
              </div>
})
