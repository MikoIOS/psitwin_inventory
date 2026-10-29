import { api } from './client'

export type DemandHorizon = 1 | 7 | 30 | 90
export interface DemandPoint { fecha: string; cantidad: number }
export interface ForecastPoint extends DemandPoint { q10: number | null; q50: number | null; q90: number | null }
export interface DemandForecast {
  estado: 'DISPONIBLE' | 'CALCULANDO' | 'SIN_HISTORIAL' | 'HISTORIAL_INSUFICIENTE' | 'MODELO_NO_DISPONIBLE' | 'ERROR_MODELO'
  id_empresa: string; id_almacen: string; id_producto: string; series_id: string
  modelo: string; tipo_modelo: string; fecha_corte: string
  historico: DemandPoint[]; predicciones: ForecastPoint[]
  horizontes: { horizonte_dias: DemandHorizon; demanda_acumulada: number; demanda_del_dia: number }[]
  stock_actual: number | null; cache: boolean; advertencias: string[]; detalle: string | null
}
export interface AnalysisMetadata {
  model: string; version: string; prediction_length: number; evaluation_only: boolean
  wape_accumulated_pct: Record<string, number>; holdout_from: string; holdout_to: string; evaluation_series: number
  runtime: { estado: string; validado: boolean; faltantes: string[]; detalle: string | null }
  advertencias: string[]
}
export interface DemandRank { unidad?: string; id_almacen: string; id_producto: string; almacen: string; producto: string; estado: string; demanda_acumulada: number | null; stock_actual: number | null; brecha_stock: number | null }
export interface DemandSummary { horizonte_dias: number; filas: DemandRank[]; series_totales: number; series_consultadas: number; completo: boolean; calculando: boolean; advertencias: string[] }
export interface HistoricalDemand {
  id_empresa: string; total: number; promedio_diario: number | null; dias_observados: number; documentos: number
  fecha_inicio: string | null; fecha_fin: string | null; serie: DemandPoint[]; advertencias: string[]
  registros: { fecha: string; id_almacen: string; id_producto: string; cantidad: number; es_imputado: boolean }[]
}
export const analisisApi = {
  historical: (query: Record<string, string | number>) => api.get<HistoricalDemand>('/analisis/historico', { query }),
  metadata: () => api.get<AnalysisMetadata>('/analisis/modelo'),
  filters: () => api.get<{ id_empresa: string; almacenes: { id: string; nombre: string }[]; productos: { id: string; nombre: string }[] }>('/analisis/filtros'),
  forecast: (warehouse: string, product: string, source = 'salidas') => api.get<DemandForecast>('/analisis/pronostico', { query: { id_almacen: warehouse, id_producto: product, fuente: source } }),
  summary: (horizon: DemandHorizon, warehouse: string, product: string, source = 'salidas') => api.get<DemandSummary>('/analisis/resumen', { query: { horizonte_dias: horizon, fuente: source, ...(warehouse ? { id_almacen: warehouse } : {}), ...(product ? { id_producto: product } : {}) } }),
}
