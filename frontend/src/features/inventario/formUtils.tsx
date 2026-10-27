/**
 * Utilidades de formulario compartidas por los módulos productos / inventario / movimientos.
 *
 * `useInlineApiError()` muestra los errores de la API DENTRO del formulario (banner), en lugar de un toast.
 * Motivo: los formularios de estos módulos viven en <Modal> (<dialog> en top-layer) y los toasts
 * quedan por debajo del backdrop mientras el modal está abierto.
 *  - 422 → errores en los campos del form (applyFieldErrors); los que no mapean van al banner.
 *  - 409 → banner "Operación no permitida" con el `detail` del backend.
 *  - 401 → nada (el cliente redirige a /login). 403 → banner "sin permiso".
 *  - resto → banner con el mensaje ya traducido por ApiError.
 */
import { useCallback, useState, type ReactNode } from 'react'
import type { FieldValues, UseFormRegisterReturn } from 'react-hook-form'
import { ApiError } from '@/api/client'
import { AlmacenSelect, RackSelect, ZonaSelect } from '@/components/selects'
import { applyFieldErrors, Field, Icon, type FormLike } from '@/components/ui'
import { cn } from '@/lib/cn'

export interface InlineError {
  titulo: string
  detalle: string
  status: number
}

export function useInlineApiError() {
  const [error, setError] = useState<InlineError | null>(null)

  const handle = useCallback(
    <T extends FieldValues>(e: unknown, opts: { titulo: string; form?: FormLike<T>; fieldMap?: Record<string, string> }) => {
      if (!(e instanceof ApiError)) {
        console.error(e)
        setError({ titulo: opts.titulo, detalle: e instanceof Error ? e.message : 'Ocurrió un error inesperado.', status: -1 })
        return
      }
      if (e.isHandledGlobally) return
      if (e.isValidation && opts.form) {
        const { applied, unmatched } = applyFieldErrors(opts.form, e, opts.fieldMap)
        const extra = Object.entries(unmatched).map(([k, v]) => `${k}: ${v}`)
        if (extra.length > 0) setError({ titulo: 'Datos no válidos', detalle: extra.join(' · '), status: e.status })
        else if (applied.length === 0) setError({ titulo: 'Datos no válidos', detalle: e.detail, status: e.status })
        else setError(null)
        return
      }
      setError({ titulo: e.isConflict ? 'Operación no permitida' : opts.titulo, detalle: e.detail, status: e.status })
    },
    [],
  )

  const clear = useCallback(() => setError(null), [])
  return { error, handle, clear }
}

export interface FormAlertProps {
  tone?: 'danger' | 'warning' | 'info'
  title?: ReactNode
  children?: ReactNode
  className?: string
}

const ALERT_TONE = {
  danger: { box: 'border-danger/30 bg-danger-soft/60', icon: 'text-danger', name: 'alert' as const },
  warning: { box: 'border-warning/30 bg-warning-soft/70', icon: 'text-warning', name: 'alert' as const },
  info: { box: 'border-info/25 bg-info-soft/60', icon: 'text-info', name: 'info' as const },
}

/** Aviso en línea dentro de formularios y diálogos. */
export function FormAlert({ tone = 'danger', title, children, className }: FormAlertProps) {
  const t = ALERT_TONE[tone]
  return (
    <div
      role={tone === 'danger' ? 'alert' : 'status'}
      className={cn('flex gap-2.5 rounded-[var(--radius-ui)] border px-3 py-2.5 text-sm', t.box, className)}
    >
      <Icon name={t.name} className={cn('mt-0.5 size-4 shrink-0', t.icon)} />
      <div className="min-w-0">
        {title && <p className="font-semibold text-fg">{title}</p>}
        {children && <div className="text-fg-muted">{children}</div>}
      </div>
    </div>
  )
}

/** Banner de error de API (usa el estado de `useInlineApiError`). */
export function ApiErrorAlert({ error }: { error: InlineError | null }) {
  if (!error) return null
  return <FormAlert title={error.titulo}>{error.detalle}</FormAlert>
}

/* ------------------------------------------------------------------ */

export interface RackCascadaProps {
  idAlmacen: string
  idZona: string
  /** Resultados de `register()` (usar `onChange` en el padre para resetear los hijos). */
  registros: { almacen: UseFormRegisterReturn; zona: UseFormRegisterReturn; rack: UseFormRegisterReturn }
  errores: { almacen?: string | undefined; zona?: string | undefined; rack?: string | undefined }
  soloDisponibles?: boolean
  legend?: string
  hint?: ReactNode
}

/** Selección de rack en cascada Almacén → Zona → Rack. */
export function RackCascada({ idAlmacen, idZona, registros, errores, soloDisponibles = false, legend = 'Ubicación', hint }: RackCascadaProps) {
  return (
    <fieldset className="rounded-md border border-border p-4">
      <legend className="label-stencil px-1">{legend}</legend>
      {hint && <p className="-mt-1 mb-3 text-xs text-fg-subtle">{hint}</p>}
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Almacén" error={errores.almacen} required>
          <AlmacenSelect {...registros.almacen} />
        </Field>
        <Field label="Zona" error={errores.zona} required>
          <ZonaSelect idAlmacen={idAlmacen || undefined} {...registros.zona} />
        </Field>
        <Field label="Rack" error={errores.rack} required>
          <RackSelect idZona={idZona || undefined} soloDisponibles={soloDisponibles} {...registros.rack} />
        </Field>
      </div>
    </fieldset>
  )
}
