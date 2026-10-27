/**
 * Contraseñas temporales para operarios (la empresa las entrega; el operario las cambia al ingresar).
 * Alfabeto sin caracteres ambiguos (0/O, 1/l/I) para dictarlas o copiarlas sin errores.
 */
const ALFABETO = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'

export function generarPasswordTemporal(longitud = 10): string {
  const n = Math.max(6, longitud)
  const bytes = new Uint32Array(n)
  crypto.getRandomValues(bytes)
  let out = ''
  for (const b of bytes) out += ALFABETO[b % ALFABETO.length]
  // Garantiza al menos un dígito (más fácil de validar por políticas externas).
  if (!/\d/.test(out)) out = out.slice(0, -1) + String(2 + (bytes[0]! % 8))
  return out
}

/** Copia texto al portapapeles. Devuelve false si el navegador no lo permite. */
export async function copiarAlPortapapeles(texto: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(texto)
      return true
    }
  } catch {
    /* sigue con el método antiguo */
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = texto
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    return ok
  } catch {
    return false
  }
}
