import type { Ref, TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'
import { controlClass, useFieldControl } from './Field'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  ref?: Ref<HTMLTextAreaElement> | undefined
}

export function Textarea({ className, rows = 3, ref, ...props }: TextareaProps) {
  const aria = useFieldControl(props)
  return <textarea ref={ref} rows={rows} {...props} {...aria} className={cn(controlClass, 'py-2 text-sm', className)} />
}
