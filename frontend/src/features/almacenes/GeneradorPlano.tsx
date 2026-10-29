/**
 * Generador de plano: el usuario indica área, estantes, refrigeradoras, etc. y el plano se
 * dibuja solo (SVG) con el estilo de un plano de tienda. Se puede descargar como PNG o SVG.
 */
import { useMemo, useRef, useState } from 'react'
import { Button, Card, Checkbox, Field, Input } from '@/components/ui'
import { AREA_MAX, AREA_MIN, generarPlano, type Elemento } from './generarPlano'

const num = (v: string, max: number) => Math.min(max, Math.max(0, Math.floor(Number(v) || 0)))

export function GeneradorPlano({ areaInicial }: { areaInicial?: number | undefined }) {
  const [area, setArea] = useState(String(Math.round(areaInicial && areaInicial >= 100 ? areaInicial : 400)))
  const [estantes, setEstantes] = useState('3')
  const [refri, setRefri] = useState('4')
  const [congel, setCongel] = useState('1')
  const [cajas, setCajas] = useState('1')
  const [conAlmacen, setConAlmacen] = useState(true)
  const [conBano, setConBano] = useState(true)
  const [estantesPared, setEstantesPared] = useState(true)
  const svgRef = useRef<SVGSVGElement>(null)

  const areaNum = Number(area)
  const areaError = !area || Number.isNaN(areaNum) || areaNum < AREA_MIN || areaNum > AREA_MAX ? `Ingresa un área entre ${AREA_MIN} y ${AREA_MAX} m².` : undefined

  const plano = useMemo(
    () =>
      generarPlano({
        areaM2: areaNum,
        estantes: num(estantes, 40),
        refrigeradoras: num(refri, 30),
        congeladores: num(congel, 20),
        cajas: num(cajas, 10),
        conAlmacen,
        conBano,
        estantesPared,
      }),
    [areaNum, estantes, refri, congel, cajas, conAlmacen, conBano, estantesPared],
  )

  const { viewBox: vb, leyenda: ley, fs, sw, wallSw } = plano
  const FUENTE = 'system-ui, -apple-system, "Segoe UI", Arial, sans-serif'

  function serializar() {
    const svg = svgRef.current
    if (!svg) return null
    const clon = svg.cloneNode(true) as SVGSVGElement
    const ancho = 1600
    clon.setAttribute('width', String(ancho))
    clon.setAttribute('height', String(Math.round((ancho * vb.h) / vb.w)))
    return { texto: new XMLSerializer().serializeToString(clon), ancho, alto: Math.round((ancho * vb.h) / vb.w) }
  }

  function descargar(blob: Blob, nombre: string) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = nombre
    a.click()
    URL.revokeObjectURL(url)
  }

  function descargarSvg() {
    const s = serializar()
    if (s) descargar(new Blob([s.texto], { type: 'image/svg+xml' }), 'plano-almacen.svg')
  }

  function descargarPng() {
    const s = serializar()
    if (!s) return
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = s.ancho * 2
      canvas.height = s.alto * 2
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((b) => b && descargar(b, 'plano-almacen.png'))
    }
    img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(s.texto)}`
  }

  return (
    <Card
      as="section"
      className="mt-8"
      eyebrow="Herramienta"
      title="Generador de plano"
      description="Indica el área y los muebles; el plano se dibuja solo y se actualiza al cambiar cualquier dato."
      actions={
        <>
          <Button variant="secondary" onClick={descargarPng} disabled={!!areaError}>
            Descargar PNG
          </Button>
          <Button variant="ghost" onClick={descargarSvg} disabled={!!areaError}>
            Descargar SVG
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Field label="Área total" error={areaError}>
          <Input type="number" inputMode="numeric" min={AREA_MIN} max={AREA_MAX} suffix="m²" value={area} onChange={(e) => setArea(e.target.value)} />
        </Field>
        <Field label="Estantes (centro)">
          <Input type="number" inputMode="numeric" min={0} max={40} value={estantes} onChange={(e) => setEstantes(e.target.value)} />
        </Field>
        <Field label="Refrigeradoras">
          <Input type="number" inputMode="numeric" min={0} max={30} value={refri} onChange={(e) => setRefri(e.target.value)} />
        </Field>
        <Field label="Congeladores">
          <Input type="number" inputMode="numeric" min={0} max={20} value={congel} onChange={(e) => setCongel(e.target.value)} />
        </Field>
        <Field label="Cajas">
          <Input type="number" inputMode="numeric" min={0} max={10} value={cajas} onChange={(e) => setCajas(e.target.value)} />
        </Field>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-3">
        <Checkbox label="Almacén" checked={conAlmacen} onChange={(e) => setConAlmacen(e.target.checked)} />
        <Checkbox label="Baño" checked={conBano} onChange={(e) => setConBano(e.target.checked)} />
        <Checkbox label="Estantes en las paredes" checked={estantesPared} onChange={(e) => setEstantesPared(e.target.checked)} />
      </div>

      {plano.avisos.length > 0 && (
        <ul className="mt-4 space-y-1 rounded-[var(--radius-ui)] border border-warning/50 bg-warning-soft p-3 text-sm text-fg" role="status">
          {plano.avisos.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}

      <figure className="mt-4 overflow-hidden rounded-[var(--radius-ui)] border border-border-strong bg-[#0b0b0b]">
        <svg
          ref={svgRef}
          xmlns="http://www.w3.org/2000/svg"
          viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
          role="img"
          aria-label={`Plano de ${Math.round(plano.W * plano.H)} m²: ${plano.leyenda.items.join(', ')}`}
          className="block h-auto w-full"
          style={{ fontFamily: FUENTE }}
        >
          <rect x={vb.x} y={vb.y} width={vb.w} height={vb.h} fill="#0b0b0b" />
          <g fill="none" stroke="#ffffff" strokeLinecap="square" strokeLinejoin="miter">
            {plano.elementos.map((el, i) => (
              <Pieza key={i} el={el} fs={fs} sw={sw} wallSw={wallSw} />
            ))}
          </g>

          {/* Leyenda */}
          <g>
            <rect x={ley.x} y={ley.y} width={ley.w} height={ley.h} fill="none" stroke="#ffffff" strokeWidth={sw} />
            <text x={ley.x + fs * 1} y={ley.y + fs * 2} fill="#ffffff" fontSize={fs * 1.25} fontWeight={600}>
              Áreas del minimarket
            </text>
            {ley.items.map((it, i) => (
              <text key={it} x={ley.x + fs * 1} y={ley.y + fs * (4.2 + i * 1.75)} fill="#ffffff" fontSize={fs}>
                {`${i + 1}.  ${it}`}
              </text>
            ))}
          </g>
        </svg>
      </figure>
      <p className="mt-2 text-xs text-fg-subtle">
        Plano esquemático de {Math.round(plano.W * 10) / 10} × {Math.round(plano.H * 10) / 10} m. La distribución es automática y aproximada.
      </p>
    </Card>
  )
}

function Pieza({ el, fs, sw, wallSw }: { el: Elemento; fs: number; sw: number; wallSw: number }) {
  switch (el.t) {
    case 'rect':
      return <rect x={el.x} y={el.y} width={el.w} height={el.h} strokeWidth={sw} />
    case 'path':
      return <path d={el.d} strokeWidth={el.pared ? wallSw : sw} />
    case 'ellipse':
      return <ellipse cx={el.cx} cy={el.cy} rx={el.rx} ry={el.ry} strokeWidth={sw} />
    case 'text': {
      const size = el.grande ? fs * 1.3 : fs
      return (
        <text x={el.x} y={el.y} textAnchor={el.anchor} fontSize={size} fill="#ffffff" stroke="none">
          {el.lines.map((l, i) => (
            <tspan key={i} x={el.x} dy={i === 0 ? 0 : size * 1.2}>
              {l}
            </tspan>
          ))}
        </text>
      )
    }
  }
}
