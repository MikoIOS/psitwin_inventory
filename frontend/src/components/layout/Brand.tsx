import { cn } from '@/lib/cn'

/** Marca PsiTwin: isotipo de nave + wordmark. `tone="dark"` para fondos oscuros (sidebar). */
export function Brand({ tone = 'dark', className }: { tone?: 'dark' | 'light'; className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <svg viewBox="0 0 32 32" className="size-8 shrink-0" aria-hidden="true">
        <rect width="32" height="32" rx="6" fill={tone === 'dark' ? 'var(--sidebar-2)' : 'var(--sidebar)'} />
        <path d="M7 23V11l9-4 9 4v12" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M11 23v-7h10v7M11 19.5h10" fill="none" stroke="var(--accent)" strokeWidth="2" />
      </svg>
      <span className="flex flex-col leading-none">
        <span className={cn('text-[1.05rem] font-bold tracking-tight', tone === 'dark' ? 'text-sidebar-fg' : 'text-fg')}>
          PsiTwin
        </span>
        <span className={cn('mt-1 font-mono text-[0.625rem] tracking-[0.18em] uppercase', tone === 'dark' ? 'text-sidebar-muted' : 'text-fg-subtle')}>
          Inventory
        </span>
      </span>
    </span>
  )
}
