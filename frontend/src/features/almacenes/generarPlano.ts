/**
 * Generador de plano de tienda / minimarket.
 * Recibe parámetros simples (área, nº de estantes, refrigeradoras…) y devuelve los elementos
 * a dibujar (en METROS) más avisos si algo no cabe. No depende de React: es una función pura.
 */

export interface PlanoParams {
  /** Área total en m². */
  areaM2: number
  /** Estantes (góndolas) en el centro de la sala. */
  estantes: number
  refrigeradoras: number
  congeladores: number
  cajas: number
  conAlmacen: boolean
  /** Estantes pegados a las paredes + mesas de frutas y verduras. */
  estantesPared: boolean
}

export type Elemento =
  | { t: 'rect'; x: number; y: number; w: number; h: number }
  | { t: 'path'; d: string; pared?: boolean }
  | { t: 'ellipse'; cx: number; cy: number; rx: number; ry: number }
  | { t: 'text'; x: number; y: number; lines: string[]; anchor: 'start' | 'middle' | 'end'; grande?: boolean }

export interface Plano {
  W: number
  H: number
  fs: number
  sw: number
  wallSw: number
  viewBox: { x: number; y: number; w: number; h: number }
  leyenda: { x: number; y: number; w: number; h: number; items: string[] }
  elementos: Elemento[]
  avisos: string[]
}

export const AREA_MIN = 100
export const AREA_MAX = 5000

export const NOMBRES_ESTANTES = [
  'Snacks y bebidas',
  'Limpieza y cuidado personal',
  'Papelería y otros',
  'Lácteos y huevos',
  'Panadería',
  'Conservas',
  'Licores',
  'Mascotas',
  'Bebés',
]

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))
const r1 = (n: number) => Math.round(n * 10) / 10

function wrap(txt: string, max = 16): string[] {
  const lines: string[] = []
  let cur = ''
  for (const w of txt.split(' ')) {
    const next = cur ? `${cur} ${w}` : w
    if (next.length > max && cur) {
      lines.push(cur)
      cur = w
    } else cur = next
  }
  if (cur) lines.push(cur)
  return lines
}

export function generarPlano(p: PlanoParams): Plano {
  const area = clamp(p.areaM2 || 0, AREA_MIN, AREA_MAX)
  const W = r1(Math.sqrt(area * 1.5))
  const H = r1(area / W)
  const fs = clamp(W / 55, 0.3, 1.2)
  const sw = clamp(W / 300, 0.04, 0.15)
  const wallSw = sw * 2.6

  const els: Elemento[] = []
  const avisos: string[] = []
  const rect = (x: number, y: number, w: number, h: number) => els.push({ t: 'rect', x, y, w, h })
  const path = (d: string, pared = false) => els.push({ t: 'path', d, pared })
  const text = (x: number, y: number, txt: string, anchor: 'start' | 'middle' | 'end' = 'middle', grande = false, max = 16) =>
    els.push({ t: 'text', x, y, lines: wrap(txt, max), anchor, grande })
  /** Divisiones internas de un mueble (celdas). */
  const celdas = (x: number, y: number, w: number, h: number, n: number, vertical: boolean) => {
    for (let i = 1; i < n; i++) {
      if (vertical) path(`M ${x + (w * i) / n} ${y} L ${x + (w * i) / n} ${y + h}`)
      else path(`M ${x} ${y + (h * i) / n} L ${x + w} ${y + (h * i) / n}`)
    }
  }

  const nEst = Math.max(0, Math.floor(p.estantes))
  const nFr0 = Math.max(0, Math.floor(p.refrigeradoras))
  const nCo0 = Math.max(0, Math.floor(p.congeladores))
  const nCaja = Math.max(0, Math.floor(p.cajas))
  const pared = p.estantesPared

  const hayBanda = p.conAlmacen || nFr0 > 0 || nCo0 > 0
  const D = hayBanda ? clamp(H * 0.2, 3, 5) : 0
  const aw = p.conAlmacen ? clamp(W * 0.2, 3, 8) : 0

  /* ---------------- Paredes exteriores y entrada ---------------- */
  const gap = 2.4
  const ex = r1(W * 0.4)
  path(`M ${ex} ${H} L 0 ${H} L 0 0 L ${W} 0 L ${W} ${H} L ${ex + gap} ${H}`, true)
  const rd = gap / 2
  path(`M ${ex} ${H} L ${ex} ${H - rd}`)
  path(`M ${ex + rd} ${H} A ${rd} ${rd} 0 0 0 ${ex} ${H - rd}`)
  path(`M ${ex + gap} ${H} L ${ex + gap} ${H - rd}`)
  path(`M ${ex + rd} ${H} A ${rd} ${rd} 0 0 1 ${ex + gap} ${H - rd}`)
  const cxE = ex + rd
  path(`M ${cxE} ${H + 2.5} L ${cxE} ${H + 0.9} M ${cxE - 0.4} ${H + 1.4} L ${cxE} ${H + 0.9} L ${cxE + 0.4} ${H + 1.4}`)
  text(cxE, H + 3.5, 'Entrada', 'middle', true)

  /* ---------------- Almacén ---------------- */
  if (p.conAlmacen) {
    const r = 1.2
    path(`M ${aw} 0 L ${aw} ${D}`, true)
    path(`M 0 ${D} L ${aw - r} ${D}`, true)
    path(`M ${aw} ${D} L ${aw} ${D - r}`)
    path(`M ${aw - r} ${D} A ${r} ${r} 0 0 1 ${aw} ${D - r}`)
    rect(0.4, 0.4, aw * 0.5, 0.45)
    const hv = Math.min(D - 2.2, 2.4)
    rect(0.4, 1.2, 0.75, hv)
    celdas(0.4, 1.2, 0.75, hv, 2, false)
    rect(aw - 1.0, 0.4, 0.6, 0.6)
    text(aw * 0.58, D * 0.52, 'Almacén')
  }

  /* ---------------- Franja superior: refrigeradoras y congeladores ---------------- */
  let nFr = nFr0
  let nCo = nCo0
  if (nFr0 > 0 || nCo0 > 0) {
    const xIni = aw
    const disp = W - bw - xIni - 0.8
    const aFr = 1.0
    const aCo = 2.2
    const total = nFr0 * aFr + nCo0 * aCo + (nFr0 && nCo0 ? 0.6 : 0)
    if (total > disp) {
      const f = Math.max(0, disp) / total
      nFr = Math.floor(nFr0 * f)
      nCo = Math.floor(nCo0 * f)
      if (nFr0 > 0 && nFr === 0 && disp >= aFr) nFr = 1
      if (nCo0 > 0 && nCo === 0 && disp - nFr * aFr >= aCo) nCo = 1
      avisos.push(
        `En la franja superior solo caben ${nFr} refrigeradora(s) y ${nCo} congelador(es) de los ${nFr0} y ${nCo0} pedidos. Aumenta el área para ubicar todos.`,
      )
    }
    const sobra = disp - (nFr * aFr + nCo * aCo)
    const sep = nFr && nCo ? clamp(sobra / 2, 0.6, 5) : 0
    let x = xIni + 0.4
    if (nFr > 0) {
      rect(x, 1.4, nFr * aFr, 0.8)
      celdas(x, 1.4, nFr * aFr, 0.8, nFr, true)
      text(x + (nFr * aFr) / 2, 0.95, 'Refrigeradores')
      x += nFr * aFr + sep
    }
    if (nCo > 0) {
      const x0 = x
      for (let i = 0; i < nCo; i++) {
        rect(x, 1.4, 2, 0.9)
        x += aCo
      }
      text(x0 + (nCo * aCo - 0.2) / 2, 0.95, 'Congeladores')
    }
  }

  /* ---------------- Cajas ---------------- */
  const xCaja0 = ex + gap + 1.2
  const limCaja = W - 0.6 - (pared ? 1.4 : 0)
  const colsCaja = Math.max(1, Math.floor((limCaja - xCaja0 + 0.6) / 3.0))
  const filasCaja = Math.min(2, Math.ceil(nCaja / colsCaja))
  const cajasColocadas = Math.min(nCaja, colsCaja * filasCaja)
  if (cajasColocadas < nCaja) avisos.push(`Solo caben ${cajasColocadas} de ${nCaja} cajas. Aumenta el área.`)
  for (let i = 0; i < cajasColocadas; i++) {
    const c = i % colsCaja
    const f = Math.floor(i / colsCaja)
    const x = Math.min(xCaja0 + c * 3.0, limCaja - 2.4)
    const y = H - 2.4 - f * 2.4
    rect(x, y, 2.4, 1.0)
    rect(x + 0.9, y + 0.15, 0.8, 0.55)
    rect(x + 1.85, y + 0.3, 0.25, 0.3)
  }
  if (cajasColocadas > 0) {
    const cx = Math.min(xCaja0, limCaja - 2.4) + 1.2
    text(cx, H - 0.85, 'Caja')
  }

  /* ---------------- Estantes de pared y frutas/verduras ---------------- */
  const yPared0 = (D > 0 ? D : 0) + 0.6
  let hayAbarrotes = false
  let hayFrutas = false
  let haySnacksPared = false
  let xLibreIzq = 1.5
  let xLibreDer = W - 1.5

  if (pared) {
    // Izquierda: Abarrotes
    const y1 = H - 1.4
    const len = y1 - yPared0
    if (len >= 2) {
      const n = Math.max(1, Math.round(len / 1.2))
      rect(0.3, yPared0, 0.7, len)
      celdas(0.3, yPared0, 0.7, len, n, false)
      text(1.3, (yPared0 + y1) / 2 + fs * 0.35, 'Abarrotes', 'start')
      hayAbarrotes = true
      xLibreIzq = 1.0 + 0.3 + 'Abarrotes'.length * 0.55 * fs + 0.9
    }
    // Inferior: Snacks y bebidas
    const xEnd = ex - 0.8
    const lenB = xEnd - 1.2
    if (lenB >= 2) {
      const n = Math.max(1, Math.round(lenB / 1.2))
      rect(1.2, H - 1.0, lenB, 0.7)
      celdas(1.2, H - 1.0, lenB, 0.7, n, true)
      text(1.2 + lenB / 2, H - 1.3, 'Snacks y bebidas')
      haySnacksPared = true
    }
    // Derecha: estante largo + mesas de frutas y verduras
    const yR1 = H - 0.6
    const lenR = yR1 - yPared0
    if (lenR >= 2) {
      const n = Math.max(1, Math.round(lenR / 1.2))
      rect(W - 1.0, yPared0, 0.7, lenR)
      celdas(W - 1.0, yPared0, 0.7, lenR, n, false)
      xLibreDer = W - 1.0 - 0.5
      const stackX = W - 2.9
      const yIni = yPared0 + 1.2
      const topCajas = cajasColocadas > 0 ? H - 2.4 - (filasCaja - 1) * 2.4 : H - 1.5
      const k = clamp(Math.floor((topCajas - 1.0 - yIni) / 1.5), 0, 5)
      if (k >= 1) {
        for (let i = 0; i < k; i++) {
          rect(stackX, yIni + i * 1.5, 1.4, 1.4)
          rect(stackX + 0.2, yIni + i * 1.5 + 0.2, 1.0, 1.0)
        }
        text(stackX - 0.4, yIni + (k * 1.5) / 2 - fs * 0.6, 'Frutas y verduras', 'end', false, 9)
        hayFrutas = true
        xLibreDer = stackX - 0.4 - 'Frutas y'.length * 0.55 * fs - 0.8
      }
    }
  }

  /* ---------------- Estantes centrales (góndolas) ---------------- */
  const usados: string[] = []
  let nColocados = 0
  if (nEst > 0) {
    const xL = pared ? xLibreIzq : 1.5
    const xR = pared ? xLibreDer : W - 1.5
    const yT = D > 0 ? D + 1.6 : 1.5
    const labelSp = fs * 2.4 + 0.2
    const bottomLim = H - 3.4 - (cajasColocadas > 0 ? (filasCaja - 1) * 2.4 : 0)
    const avail = bottomLim - yT
    const gw = 0.9
    // Separación mínima entre columnas: que quepa la etiqueta más larga (≈16 letras) sin pisar a la vecina.
    const pitchMin = Math.max(gw + 1.4, 16 * 0.58 * fs + 0.4)
    const colsMax = Math.floor((xR - xL) / pitchMin)
    let maxRows = 0
    for (let r = 1; r <= 4; r++) {
      const lr = (avail - r * labelSp - (r - 1) * 1.0) / r
      if (lr >= 2.5) maxRows = r
    }
    if (colsMax < 1 || maxRows < 1) {
      avisos.push('El área es muy pequeña para ubicar estantes centrales con los demás elementos. Aumenta el área o desactiva los estantes de pared.')
    } else {
      const rows = Math.min(maxRows, Math.ceil(nEst / colsMax))
      const cols = Math.min(colsMax, Math.ceil(nEst / rows))
      nColocados = Math.min(nEst, rows * cols)
      if (nColocados < nEst) avisos.push(`Solo caben ${nColocados} de los ${nEst} estantes centrales. Aumenta el área.`)
      const lrFull = (avail - rows * labelSp - (rows - 1) * 1.0) / rows
      const lr = Math.min(lrFull, 7)
      const usado = rows * (lr + labelSp) + (rows - 1) * 1.0
      const off = (avail - usado) / 2
      const paso = (xR - xL) / cols
      for (let i = 0; i < nColocados; i++) {
        const f = Math.floor(i / cols)
        const c = i % cols
        const cx = xL + (c + 0.5) * paso
        const x = cx - gw / 2
        const y = yT + off + f * (lr + labelSp + 1.0)
        rect(x, y, gw, lr)
        path(`M ${cx} ${y} L ${cx} ${y + lr}`)
        celdas(x, y, gw, lr, Math.max(2, Math.round(lr / 0.9)), false)
        const nombre = NOMBRES_ESTANTES[i % NOMBRES_ESTANTES.length] ?? 'Estante'
        usados.push(nombre)
        text(cx, y + lr + fs * 1.3, nombre)
      }
    }
  }

  /* ---------------- Leyenda ---------------- */
  const items: string[] = ['Entrada principal']
  const add = (s: string) => {
    if (!items.includes(s)) items.push(s)
  }
  if (cajasColocadas > 0) add('Caja')
  if (hayFrutas) add('Frutas y verduras')
  if (hayAbarrotes) add('Abarrotes')
  if (haySnacksPared) add('Snacks y bebidas')
  usados.forEach(add)
  if (nFr > 0) add('Refrigeradores')
  if (nCo > 0) add('Congeladores')
  if (p.conAlmacen) add('Almacén')

  const legW = fs * 18
  const legH = fs * (2.9 + 1.75 * items.length)
  const legX = W + 1.5
  const pad = Math.max(0.8, W / 30)
  const vbW = legX + legW + pad * 2
  const vbH = Math.max(H + 4.2, legH + 1) + pad

  return {
    W,
    H,
    fs,
    sw,
    wallSw,
    viewBox: { x: -pad, y: -pad, w: vbW, h: vbH },
    leyenda: { x: legX, y: 0, w: legW, h: legH, items },
    elementos: els,
    avisos,
  }
}
