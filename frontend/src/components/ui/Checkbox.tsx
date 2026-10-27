import { useId, type InputHTMLAttributes, type ReactNode, type Ref } from 'react'
import { cn } from '@/lib/cn'

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: ReactNode
  description?: ReactNode
  ref?: Ref<HTMLInputElement> | undefined
}

/** Checkbox con etiqueta clicable (área ≥ 24px). Compatible con `register()`. */
export function Checkbox({ label, description, className, id, ref, ...props }: CheckboxProps) {
  const autoId = useId()
  const cid = id ?? `cb${autoId}`
  return (
    <div className={cn('flex items-start gap-3', className)}>
      <input
        ref={ref}
        id={cid}
        type="checkbox"
        className="mt-0.5 size-5 shrink-0 cursor-pointer rounded border-border-strong accent-[var(--accent)]"
        aria-describedby={description ? `${cid}-desc` : undefined}
        {...props}
      />
      <div className="flex flex-col">
        <label htmlFor={cid} className="cursor-pointer text-sm font-medium text-fg">
          {label}
        </label>
        {description && (
          <p id={`${cid}-desc`} className="text-xs text-fg-subtle">
            {description}
          </p>
        )}
      </div>
    </div>
  )
}
