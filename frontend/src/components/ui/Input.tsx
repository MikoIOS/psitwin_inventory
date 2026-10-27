import type { InputHTMLAttributes, ReactNode, Ref } from 'react'
import { cn } from '@/lib/cn'
import { controlClass, useFieldControl } from './Field'

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: 'md' | 'lg'
  /** Texto/unidad fija a la derecha (ej. "m²", "°C", "días"). */
  suffix?: ReactNode
  ref?: Ref<HTMLInputElement> | undefined
}

/** Input compatible con `register()` de react-hook-form. */
export function Input({ size = 'md', suffix, className, ref, ...props }: InputProps) {
  const aria = useFieldControl(props)
  const input = (
    <input
      ref={ref}
      {...props}
      {...aria}
      className={cn(controlClass, size === 'lg' ? 'h-12 text-base' : 'h-10 text-sm', suffix && 'pr-12', props.type === 'number' && 'tabular', className)}
    />
  )
  if (!suffix) return input
  return (
    <div className="relative">
      {input}
      <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center font-mono text-xs text-fg-subtle">
        {suffix}
      </span>
    </div>
  )
}
