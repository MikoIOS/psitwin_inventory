import type { ReactNode } from 'react'
import { Brand } from '@/components/layout/Brand'

/** Layout de login/registro: panel de marca a la izquierda (≥ lg) y formulario a la derecha. */
export function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle?: ReactNode; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="grid min-h-dvh bg-bg lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="relative hidden overflow-hidden bg-sidebar text-sidebar-fg lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="hazard-stripe absolute inset-x-0 top-0 h-2" aria-hidden="true" />
        <Brand />
        <div className="max-w-md">
          <p className="font-mono text-xs tracking-[0.18em] text-accent uppercase">Control de almacén</p>
          <p className="mt-3 text-3xl leading-tight font-semibold text-white">
            Cada unidad, en su rack.
            <br />
            Cada movimiento, registrado.
          </p>
          <p className="mt-4 text-sm text-sidebar-muted">
            Almacenes, zonas y racks; inventario por ubicación; reposición con proveedores y recepción de mercadería en un solo
            panel.
          </p>
        </div>
        {/* Rejilla tipo plano de planta */}
        <div className="grid grid-cols-6 gap-1.5 opacity-60" aria-hidden="true">
          {Array.from({ length: 18 }, (_, i) => (
            <span
              key={i}
              className={
                i % 7 === 3 ? 'h-6 rounded-sm bg-accent/80' : i % 5 === 0 ? 'h-6 rounded-sm bg-sidebar-2' : 'h-6 rounded-sm border border-white/10'
              }
            />
          ))}
        </div>
      </aside>

      <main className="flex flex-col items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Brand tone="light" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-fg-muted">{subtitle}</p>}
          <div className="mt-8">{children}</div>
          {footer && <div className="mt-8 border-t border-border pt-5 text-sm text-fg-muted">{footer}</div>}
        </div>
      </main>
    </div>
  )
}
