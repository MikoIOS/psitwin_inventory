import { useState } from 'react'
import { inventarioConsultasApi, type FiltrosInventario, type ReporteAccion } from '@/api/inventarioConsultas'
import { Button } from '@/components/ui'
import { useSaikiSession } from './SaikiSession'

export function ReporteSaiki() {
  const session = useSaikiSession()
  const [error,setError] = useState(''), [busy,setBusy] = useState(false)
  const action = session.result?.data?.reporte_accion as ReporteAccion | undefined
  const download = session.result?.data?.reporte_descarga as { formato?: 'pdf'|'xlsx'; filtros: FiltrosInventario } | undefined
  const page = session.result?.data?.paginacion as { pagina: number; limite: number; total: number } | undefined
  async function getFile(format: 'pdf'|'xlsx') { if (!download) return; setError('');setBusy(true); try { await inventarioConsultasApi.descargar(format,download.filtros) } catch {setError('No se pudo generar la descarga. Puedes reintentar desde Inventario.')} finally {setBusy(false)} }
  return <>
    {action && ['ELEGIR_FORMATO','CONFIRMAR'].includes(action.estado) && <div className="mx-4 mb-3 rounded-lg border border-violet-400/30 p-3 text-sm"><p>Correo registrado: {action.destinatario}</p><p>Alcance: {action.alcance}</p><div className="mt-3 flex flex-wrap gap-2">{action.estado === 'ELEGIR_FORMATO' ? <><Button disabled={session.pending} onClick={() => void session.send('Excel')}>Excel</Button><Button disabled={session.pending} onClick={() => void session.send('PDF')}>PDF</Button></> : <Button disabled={session.pending} onClick={() => void session.send('Sí, envíalo')}>Confirmar envío</Button>}<Button variant="ghost" disabled={session.pending} onClick={() => void session.send('Cancelar')}>Cancelar envío</Button></div></div>}
    {download && <div className="mx-4 mb-3 flex flex-wrap gap-2">{(['xlsx','pdf'] as const).filter(format => !download.formato || format === download.formato).map(format => <Button key={format} disabled={busy} onClick={() => void getFile(format)}>Descargar {format === 'xlsx' ? 'Excel' : 'PDF'}</Button>)}</div>}
    {page && page.pagina * page.limite < page.total && <div className="mx-4 mb-3"><Button disabled={session.pending} onClick={() => void session.send(`Enumera todos los productos de mi inventario, página ${page.pagina+1}.`,undefined,{page:page.pagina+1})}>Siguiente página de productos</Button></div>}
    {error && <p role="alert" className="mx-4 mb-3 text-sm text-danger">{error}</p>}
  </>
}
