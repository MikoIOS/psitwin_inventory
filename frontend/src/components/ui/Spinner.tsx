import { cn } from '@/lib/cn'

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  /** Texto accesible (no visible). */
  label?: string
  className?: string
}

const SIZES = { sm: 'size-4 border-2', md: 'size-6 border-2', lg: 'size-10 border-[3px]' }

export function Spinner({ size = 'md', label = 'Cargando', className }: SpinnerProps) {
  return (
    <span role="status" className={cn('inline-flex', className)}>
      <span
        className={cn('animate-spin rounded-full border-current border-r-transparent opacity-80', SIZES[size])}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </span>
  )
}

/** Bloque de carga centrado para secciones o páginas. */
export function LoadingBlock({ label = 'Cargando…', className }: { label?: string; className?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-16 text-fg-muted', className)}>
      <Spinner size="lg" label={label} className="text-accent" />
      <p className="text-sm">{label}</p>
    </div>
  )
}
