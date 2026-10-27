/**
 * Field = label + control + ayuda + error. Conecta automáticamente id, aria-invalid y
 * aria-describedby con Input / Select / Textarea / Checkbox hijos (vía contexto).
 *
 *   <Field label="Nombre" error={errors.nombre?.message} required>
 *     <Input {...register('nombre')} />
 *   </Field>
 */
import { createContext, use, useId, type ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface FieldCtx {
  id: string
  describedBy: string | undefined
  invalid: boolean
  required: boolean
}

const FieldContext = createContext<FieldCtx | null>(null)

/** Props ARIA para un control dentro de <Field>. Los props explícitos tienen prioridad. */
export function useFieldControl(props: { id?: string | undefined; 'aria-describedby'?: string | undefined; 'aria-invalid'?: unknown; required?: boolean | undefined }) {
  const ctx = use(FieldContext)
  return {
    id: props.id ?? ctx?.id,
    'aria-describedby': props['aria-describedby'] ?? ctx?.describedBy,
    'aria-invalid': (props['aria-invalid'] as boolean | undefined) ?? (ctx?.invalid ? true : undefined),
    required: props.required ?? (ctx?.required || undefined),
  }
}

export interface FieldProps {
  label: ReactNode
  error?: string | undefined
  hint?: ReactNode
  required?: boolean
  /** id del control; si no se pasa se genera uno. */
  id?: string
  className?: string
  /** Oculta visualmente la etiqueta (sigue siendo accesible). */
  hideLabel?: boolean
  children: ReactNode
}

export function Field({ label, error, hint, required = false, id, className, hideLabel, children }: FieldProps) {
  const autoId = useId()
  const controlId = id ?? `f${autoId}`
  const hintId = hint ? `${controlId}-hint` : undefined
  const errorId = error ? `${controlId}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <FieldContext value={{ id: controlId, describedBy, invalid: !!error, required }}>
      <div className={cn('flex flex-col gap-1.5', className)}>
        <label htmlFor={controlId} className={cn('text-sm font-medium text-fg', hideLabel && 'sr-only')}>
          {label}
          {required && (
            <span className="ml-0.5 text-danger" aria-hidden="true">
              *
            </span>
          )}
        </label>
        {children}
        {hint && !error && (
          <p id={hintId} className="text-xs text-fg-subtle">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="flex items-start gap-1 text-xs font-medium text-danger" role="alert">
            {error}
          </p>
        )}
      </div>
    </FieldContext>
  )
}

/** Clases compartidas por los controles de formulario. */
export const controlClass = cn(
  'w-full rounded-[var(--radius-ui)] border border-border-strong bg-surface px-3 text-fg',
  'placeholder:text-fg-subtle transition-colors',
  'hover:border-fg-subtle focus-visible:border-focus',
  'disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-fg-subtle',
  'aria-[invalid=true]:border-danger aria-[invalid=true]:bg-danger-soft/40',
)
