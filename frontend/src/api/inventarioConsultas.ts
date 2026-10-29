import { useQuery } from '@tanstack/react-query'
import { api, API_URL, ApiError } from './client'
import { getToken } from '@/lib/storage'
export type FiltrosInventario = { id_almacen?: string; id_zona?: string; id_rack?: string; id_nivel?: string; id_producto?: string; busqueda?: string; estado?: string }
export interface UbicacionStock { id_detalle_inventario: string; id_producto: string; producto: string; familia: string; categoria: string; unidad: string; stock_actual: number; stock_minimo: number | null; stock_maximo: number | null; estado: string; id_almacen: string; almacen: string; id_zona: string; zona: string; id_rack: string; rack: string; id_nivel: string | null; nivel: number | null; ubicacion_valida: boolean; rechazado?: boolean }
export interface AlertaUbicacion { id_producto?: string; id_detalle_inventario?: string; id_zona?: string; id_rack?: string; id_nivel?: string; producto?: string; tipo: string; observacion: string; ubicacion?: string }
export interface Plano { almacen: { id: string; nombre: string }; zonas: { id: string; id_zona?: string; nombre: string; codigo?: string; max_racks?: number; capacidad: number; estado?: string }[]; racks: { id_rack: string; id_zona: string; codigo: string; max_niveles: number; numero_niveles?: number; tipo_rack?: string; fecha_creacion?: string; estado: string; capacidad: number }[]; niveles: { id_nivel: string; id_rack: string; numero: number; codigo: string; estado?: string; productos?: string[]; monitoreo?: string; sensores?: import('./dispositivos').Dispositivo[] }[]; inventario: UbicacionStock[]; alertas: AlertaUbicacion[]; generado_en: string }
export interface ReporteAccion { id_reporte: string; estado: string; formato: 'pdf' | 'xlsx' | null; destinatario: string; alcance: string; filtros: FiltrosInventario; resumen: { productos_distintos: number }; codigo_error?: string | null }
export const inventarioConsultasApi = {
  plano: (id: string) => api.get<Plano>(`/almacenes/${encodeURIComponent(id)}/plano`),
  habilitar: (id: string) => api.post(`/racks/${encodeURIComponent(id)}/habilitar-niveles`),
  destinatario: () => api.get<{ correo: string }>('/inventario-reportes/destinatario'),
  solicitar: (formato: 'pdf' | 'xlsx', filtros: FiltrosInventario, clave_idempotencia: string) => api.post<ReporteAccion>('/inventario-reportes/solicitudes', { formato, filtros, clave_idempotencia }),
  confirmar: (id: string) => api.post<ReporteAccion>(`/inventario-reportes/envios/${encodeURIComponent(id)}/confirmar`, { confirmar: true }),
  cancelar: (id: string) => api.post(`/inventario-reportes/envios/${encodeURIComponent(id)}/cancelar`),
  async descargar(formato: 'pdf' | 'xlsx', filtros: FiltrosInventario) {
    const query = new URLSearchParams({ formato, ...Object.fromEntries(Object.entries(filtros).filter(([, value]) => !!value)) })
    const response = await fetch(`${API_URL}/inventario-reportes/exportar?${query}`, { headers: { Authorization: `Bearer ${getToken() ?? ''}` } })
    if (!response.ok) throw await ApiError.fromResponse(response)
    const blob = await response.blob(), url = URL.createObjectURL(blob)
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `inventario.${formato}`; document.body.append(anchor); anchor.click(); anchor.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
}
export const usePlano = (id: string) => useQuery({ queryKey: ['plano', id], queryFn: () => inventarioConsultasApi.plano(id), enabled: !!id, refetchInterval: 5000 })
