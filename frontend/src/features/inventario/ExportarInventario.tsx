import { useState } from 'react'
import { inventarioConsultasApi, type FiltrosInventario, type ReporteAccion } from '@/api/inventarioConsultas'
import { ApiError } from '@/api/client'
import { Button, Modal } from '@/components/ui'
import { useRol } from '@/auth/useRol'

export function ExportarInventario({ filtros }: { filtros: FiltrosInventario }) {
  const { esEmpresa } = useRol()
  const [open,setOpen] = useState(false), [busy,setBusy] = useState(false), [error,setError] = useState(''), [status,setStatus] = useState('')
  const [action,setAction] = useState<ReporteAccion | null>(null)
  const [key,setKey] = useState(() => crypto.randomUUID())
  async function run(work: () => Promise<void>, text: string) { setError('');setBusy(true);setStatus(text);try {await work()} catch(e) {setError(e instanceof ApiError ? e.detail : 'No se pudo completar el reporte.');setStatus('')} finally {setBusy(false)} }
  return <><Button variant="secondary" onClick={() => {setOpen(true);setAction(null);setError('');setStatus('');setKey(crypto.randomUUID())}}>Exportar inventario</Button><Modal open={open} onClose={() => setOpen(false)} title="Exportar resumen de inventario" dismissable={!busy}>
    <p className="mb-4 text-sm">Se respetan el almacén, la búsqueda y el estado seleccionados. Las cantidades se mantienen separadas por unidad.</p>
    {!action && <div className="grid gap-3 sm:grid-cols-2">{(['xlsx','pdf'] as const).map(format => <div key={format} className="space-y-2 rounded-lg border border-border p-3"><Button disabled={busy} fullWidth onClick={() => void run(async () => {await inventarioConsultasApi.descargar(format,filtros);setStatus('Archivo generado. La descarga se ha solicitado al navegador.')},'Generando archivo…')}>Descargar {format === 'xlsx' ? 'Excel' : 'PDF'}</Button>{esEmpresa && <Button variant="secondary" fullWidth disabled={busy} onClick={() => void run(async () => {setAction(await inventarioConsultasApi.solicitar(format,filtros,key));setStatus('Confirma el destinatario y el alcance antes del envío.')},'Preparando reporte…')}>Enviar {format === 'xlsx' ? 'Excel' : 'PDF'} al correo</Button>}</div>)}</div>}
    {action && <div className="space-y-3 rounded-lg border border-border p-4"><p>Correo registrado: <strong>{action.destinatario}</strong></p><p>Formato: {action.formato?.toUpperCase()} · Alcance: {action.alcance}</p><p>{action.resumen.productos_distintos} productos distintos.</p><p>Estado: {action.estado}</p>{action.estado === 'CONFIRMAR' && <div className="flex gap-3"><Button disabled={busy} onClick={() => void run(async () => {const next=await inventarioConsultasApi.confirmar(action.id_reporte);setAction(next);setStatus(next.estado === 'ACEPTADO_SMTP' ? 'Envío aceptado por el servidor SMTP; no confirma recepción en la bandeja de entrada.' : next.estado === 'REVISAR_ENVIO' ? 'Confirmación SMTP desconocida. No se repetirá automáticamente.' : `No se completó el envío: ${next.codigo_error ?? next.estado}`)},'Generando archivo y enviando correo…')}>Confirmar envío</Button><Button disabled={busy} variant="ghost" onClick={() => void run(async () => {await inventarioConsultasApi.cancelar(action.id_reporte);setAction(null);setKey(crypto.randomUUID());setStatus('Envío cancelado.')},'Cancelando…')}>Cancelar envío</Button></div>}</div>}
    {status && <p role="status" className="mt-4 text-sm">{status}</p>}{error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}
  </Modal></>
}
