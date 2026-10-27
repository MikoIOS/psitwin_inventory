/**
 * Formulario de almacén (crear / editar). Reutilizado por el onboarding y el módulo de almacenes.
 *
 *   const crear = useCreateAlmacen()
 *   <AlmacenForm submitLabel="Crear almacén" onSubmit={(body) => crear.mutateAsync(body)} onSuccess={...} />
 *
 * `onSubmit` debe devolver una promesa; si rechaza, el form muestra el error (422 en campos, resto en toast).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { buscarDireccion, direccionDe, type Lugar } from '@/api/geocoding'
import type { Almacen, AlmacenUpdate } from '@/api/types'
import { Button, Field, Input, Select, useApiErrorHandler } from '@/components/ui'
import { numero, numStr, texto } from '@/lib/zod'

export const TIPOS_ALMACEN = ['Alimentos', 'General', 'Secos', 'Refrigerado', 'Congelado', 'Mixto', 'Cross-docking', 'Materia prima', 'Producto terminado']

export const almacenSchema = z.object({
  nombre: texto({ min: 2, max: 100 }),
  tipo_almacen: texto({ min: 2, max: 100 }),
  area_m2: numero({ mayorQue: 0 }),
  aforo: numero({ min: 0, entero: true }),
  // Obligatorias en el backend: decimal con máx. 6 decimales.
  latitud: numero({ min: -90, max: 90, maxDecimales: 6 }),
  longitud: numero({ min: -180, max: 180, maxDecimales: 6 }),
})

export type AlmacenFormInput = z.input<typeof almacenSchema>
export type AlmacenFormOutput = z.output<typeof almacenSchema>

// Garantiza en compilación que la salida del form coincide con el body del backend.
const _check: (v: AlmacenFormOutput) => AlmacenUpdate = (v) => v
void _check

export function almacenDefaults(a?: Almacen | null): AlmacenFormInput {
  return {
    nombre: a?.nombre ?? '',
    tipo_almacen: a?.tipo_almacen ?? 'Alimentos',
    area_m2: numStr(a?.area_m2),
    aforo: numStr(a?.aforo),
    latitud: numStr(a?.latitud),
    longitud: numStr(a?.longitud),
  }
}

export interface AlmacenFormProps {
  almacen?: Almacen | null
  onSubmit: (body: AlmacenUpdate) => Promise<unknown>
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
  /** id del <form> (para botones de envío fuera del form, ej. en el footer de un Modal). */
  formId?: string
  /** Oculta los botones propios (cuando se usan los del Modal). */
  hideActions?: boolean
}

export function AlmacenForm({ almacen, onSubmit, onSuccess, onCancel, submitLabel = 'Guardar', formId, hideActions }: AlmacenFormProps) {
  const handleError = useApiErrorHandler()
  const [ubicando, setUbicando] = useState(false)
  const form = useForm<AlmacenFormInput, unknown, AlmacenFormOutput>({
    resolver: zodResolver(almacenSchema),
    defaultValues: almacenDefaults(almacen),
  })
  const { register, handleSubmit, formState, setValue, control } = form
  const err = formState.errors
  const [latStr, lonStr, tipoActual] = useWatch({ control, name: ['latitud', 'longitud', 'tipo_almacen'] })
  const lat = Number(latStr)
  const lon = Number(lonStr)
  const hayPunto = latStr !== '' && lonStr !== '' && Math.abs(lat) <= 90 && Math.abs(lon) <= 180
  const [avisoUbicacion, setAvisoUbicacion] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [buscando, setBuscando] = useState(false)
  const [resultados, setResultados] = useState<Lugar[] | null>(null)
  const [direccion, setDireccion] = useState<string | null>(null)

  const fijarPunto = (la: number, lo: number) => {
    setValue('latitud', la.toFixed(6), { shouldValidate: true, shouldDirty: true })
    setValue('longitud', lo.toFixed(6), { shouldValidate: true, shouldDirty: true })
  }

  // Dirección (calle) del punto elegido, con una pequeña espera para no consultar en cada tecla.
  useEffect(() => {
    if (!hayPunto) return
    let vigente = true
    const t = window.setTimeout(() => {
      direccionDe(lat, lon)
        .then((d) => vigente && setDireccion(d))
        .catch(() => vigente && setDireccion(null))
    }, 600)
    return () => {
      vigente = false
      window.clearTimeout(t)
    }
  }, [hayPunto, lat, lon])

  const buscar = async () => {
    if (busqueda.trim().length < 3) return
    setBuscando(true)
    setAvisoUbicacion(null)
    try {
      const r = await buscarDireccion(busqueda.trim())
      setResultados(r)
      if (r.length === 1) fijarPunto(r[0]!.lat, r[0]!.lon)
    } catch {
      setAvisoUbicacion('No se pudo buscar la dirección. Revisa tu conexión.')
    } finally {
      setBuscando(false)
    }
  }

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values)
      onSuccess?.()
    } catch (e) {
      handleError(e, { form, title: 'No se pudo guardar el almacén' })
    }
  })

  const usarMiUbicacion = () => {
    if (!('geolocation' in navigator)) {
      setAvisoUbicacion('Este navegador no permite obtener tu ubicación. Busca la dirección.')
      return
    }
    setUbicando(true)
    setAvisoUbicacion(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        fijarPunto(pos.coords.latitude, pos.coords.longitude)
        setUbicando(false)
      },
      (e) => {
        setUbicando(false)
        setAvisoUbicacion(
          e.code === e.PERMISSION_DENIED
            ? 'Permiso de ubicación denegado. Actívalo en el navegador o busca la dirección.'
            : 'No se pudo obtener tu ubicación en este equipo. Busca la dirección.',
        )
      },
      { timeout: 15_000, enableHighAccuracy: true },
    )
  }

  return (
    <form id={formId} onSubmit={submit} noValidate className="flex flex-col gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nombre del almacén" error={err.nombre?.message} required className="sm:col-span-2">
          <Input placeholder="Almacén Principal" {...register('nombre')} />
        </Field>
        <Field label="Tipo de almacén" error={err.tipo_almacen?.message} required>
          <Select
            options={[...new Set([...TIPOS_ALMACEN, ...(tipoActual ? [tipoActual] : [])])].map((t) => ({ value: t, label: t }))}
            placeholder={false}
            {...register('tipo_almacen')}
          />
        </Field>
        <Field label="Área" error={err.area_m2?.message} required>
          <Input type="number" inputMode="decimal" step="any" min={0} suffix="m²" placeholder="500" {...register('area_m2')} />
        </Field>
        <Field label="Aforo" error={err.aforo?.message} required hint="Número máximo de personas.">
          <Input type="number" inputMode="numeric" step={1} min={0} suffix="pers." placeholder="40" {...register('aforo')} />
        </Field>
      </div>

      <fieldset className="rounded-md border border-border p-4">
        <legend className="label-stencil px-1">Ubicación</legend>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            aria-label="Buscar dirección"
            placeholder="Busca una calle o dirección (ej. Av. Arequipa 1200, Lima)"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter') return
              e.preventDefault()
              void buscar()
            }}
          />
          <Button variant="secondary" onClick={() => void buscar()} loading={buscando}>
            Buscar
          </Button>
          <Button variant="secondary" icon="pin" onClick={usarMiUbicacion} loading={ubicando}>
            Mi ubicación
          </Button>
        </div>
        {avisoUbicacion && (
          <p role="alert" className="mt-2 text-xs text-danger">
            {avisoUbicacion}
          </p>
        )}
        {resultados && (
          <ul className="mt-2 divide-y divide-border rounded-md border border-border text-sm">
            {resultados.length === 0 && <li className="px-3 py-2 text-fg-subtle">Sin resultados. Prueba con otra dirección.</li>}
            {resultados.map((r) => (
              <li key={`${r.lat},${r.lon}`}>
                <button
                  type="button"
                  className="w-full px-3 py-2 text-left hover:bg-surface-2"
                  onClick={() => {
                    fijarPunto(r.lat, r.lon)
                    setResultados(null)
                  }}
                >
                  {r.nombre}
                </button>
              </li>
            ))}
          </ul>
        )}

        {/* ponytail: mapa de OpenStreetMap embebido (sin dependencias); no permite elegir el punto con un clic.
            Si hace falta, cambiar a Leaflet con marcador arrastrable. */}
        {hayPunto && (
          <>
            <iframe
              title="Mapa de la ubicación del almacén"
              className="mt-3 h-64 w-full rounded-md border border-border"
              loading="lazy"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.004},${lat - 0.003},${lon + 0.004},${lat + 0.003}&layer=mapnik&marker=${lat},${lon}`}
            />
            {direccion && <p className="mt-1 text-xs text-fg-muted">{direccion}</p>}
          </>
        )}

        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Field label="Latitud" error={err.latitud?.message} required>
            <Input type="number" inputMode="decimal" step="any" placeholder="-12.046374" className="font-mono" {...register('latitud')} />
          </Field>
          <Field label="Longitud" error={err.longitud?.message} required>
            <Input type="number" inputMode="decimal" step="any" placeholder="-77.042793" className="font-mono" {...register('longitud')} />
          </Field>
        </div>
      </fieldset>

      {!hideActions && (
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          {onCancel && (
            <Button variant="secondary" onClick={onCancel} disabled={formState.isSubmitting}>
              Cancelar
            </Button>
          )}
          <Button type="submit" loading={formState.isSubmitting} size="lg" className="sm:h-10 sm:text-sm">
            {submitLabel}
          </Button>
        </div>
      )}
    </form>
  )
}
