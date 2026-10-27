/** Formateadores en español (Perú). Todos toleran null/undefined devolviendo "—". */
const LOCALE = 'es-PE'
const VACIO = '—'

const fmtFecha = new Intl.DateTimeFormat(LOCALE, { day: '2-digit', month: 'short', year: 'numeric' })
const fmtFechaHora = new Intl.DateTimeFormat(LOCALE, {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})
const fmtNumero = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 3 })
const fmtMoneda = new Intl.NumberFormat(LOCALE, { style: 'currency', currency: 'PEN' })

function toDate(v: string | Date | null | undefined): Date | null {
  if (!v) return null
  const d = v instanceof Date ? v : new Date(v)
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatFecha(v: string | Date | null | undefined): string {
  const d = toDate(v)
  return d ? fmtFecha.format(d) : VACIO
}

export function formatFechaHora(v: string | Date | null | undefined): string {
  const d = toDate(v)
  return d ? fmtFechaHora.format(d) : VACIO
}

export function formatNumero(v: number | null | undefined, unidad?: string): string {
  if (v === null || v === undefined || Number.isNaN(v)) return VACIO
  return unidad ? `${fmtNumero.format(v)} ${unidad}` : fmtNumero.format(v)
}

export function formatMoneda(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return VACIO
  return fmtMoneda.format(v)
}

/** Primeros 8 caracteres de un UUID, para mostrar como código corto. */
export function shortId(id: string | null | undefined): string {
  return id ? id.slice(0, 8).toUpperCase() : VACIO
}

export function textoOVacio(v: string | null | undefined): string {
  return v && v.trim() !== '' ? v : VACIO
}

/** ISO → valor para <input type="datetime-local"> (hora local). */
export function isoToDatetimeLocal(iso: string | null | undefined): string {
  const d = toDate(iso)
  if (!d) return ''
  const off = d.getTimezoneOffset() * 60_000
  return new Date(d.getTime() - off).toISOString().slice(0, 16)
}

/** Valor de <input type="datetime-local"> → ISO UTC (o null si vacío). */
export function datetimeLocalToIso(v: string | null | undefined): string | null {
  if (!v) return null
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? null : d.toISOString()
}

/** "-12.04637, -77.04279" (o "—" si faltan / no son números). */
export function formatCoordenadas(lat: number | null | undefined, lon: number | null | undefined, decimales = 5): string {
  if (typeof lat !== 'number' || typeof lon !== 'number' || !Number.isFinite(lat) || !Number.isFinite(lon)) return '—'
  return `${lat.toFixed(decimales)}, ${lon.toFixed(decimales)}`
}
