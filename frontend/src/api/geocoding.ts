/**
 * Búsqueda de direcciones con OpenStreetMap (Nominatim). Servicio público: uso ligero, una búsqueda por clic.
 */
export interface Lugar {
  nombre: string
  lat: number
  lon: number
}

const BASE = 'https://nominatim.openstreetmap.org'

export async function buscarDireccion(q: string): Promise<Lugar[]> {
  const res = await fetch(`${BASE}/search?format=jsonv2&limit=5&accept-language=es&q=${encodeURIComponent(q)}`)
  if (!res.ok) throw new Error('No se pudo buscar la dirección')
  const data = (await res.json()) as { display_name: string; lat: string; lon: string }[]
  return data.map((d) => ({ nombre: d.display_name, lat: Number(d.lat), lon: Number(d.lon) }))
}

/** Nombre de la calle / dirección de unas coordenadas; null si no se puede resolver. */
export async function direccionDe(lat: number, lon: number): Promise<string | null> {
  const res = await fetch(`${BASE}/reverse?format=jsonv2&accept-language=es&lat=${lat}&lon=${lon}`)
  if (!res.ok) return null
  const data = (await res.json()) as { display_name?: string }
  return data.display_name ?? null
}
