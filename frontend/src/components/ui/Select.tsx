import type { ReactNode, Ref, SelectHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'
import { controlClass, useFieldControl } from './Field'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  options?: readonly SelectOption[]
  /** Primera opción vacía (value=""). Por defecto "Selecciona…". Pasar `false` para omitirla. */
  placeholder?: string | false
  size?: 'md' | 'lg'
  ref?: Ref<HTMLSelectElement> | undefined
  children?: ReactNode
}

/** Select nativo estilizado (accesible y usable en móvil). Compatible con `register()`. */
export function Select({ options, placeholder = 'Selecciona…', size = 'md', className, children, ref, ...props }: SelectProps) {
  const aria = useFieldControl(props)
  return (
    <div className="relative">
      <select
        ref={ref}
        {...props}
        {...aria}
        className={cn(controlClass, 'appearance-none pr-9', size === 'lg' ? 'h-12 text-base' : 'h-10 text-sm', className)}
      >
        {placeholder !== false && <option value="">{placeholder}</option>}
        {options?.map((o) => (
          <option key={o.value} value={o.value} disabled={o.disabled}>
            {o.label}
          </option>
        ))}
        {children}
      </select>
      <svg
        className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-fg-subtle"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <path d="m6 9 6 6 6-6" />
      </svg>
    </div>
  )
}
