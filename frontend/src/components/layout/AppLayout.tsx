/**
 * Layout principal: sidebar fijo en ≥ lg; barra superior + drawer en móvil/tablet.
 * Las páginas se renderizan en <Outlet /> dentro de <main id="contenido">. El menú se filtra por rol (`navigation.ts`).
 * Para EMPRESA / OPERARIO abre el WebSocket de monitoreo (`MonitoreoProvider`): toast al abrirse una alerta y
 * contador de alertas abiertas en el ítem «Monitoreo».
 */
import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigation } from 'react-router'
import { useSession } from '@/auth/SessionContext'
import { useEmpresa } from '@/auth/useEmpresa'
import { Button, Icon, useToast } from '@/components/ui'
import { cn } from '@/lib/cn'
import { MonitoreoProvider, useMonitoreoVivo } from '@/api/monitoreo'
import { Brand } from './Brand'
import { etiquetaAlerta } from '@/features/monitoreo/monitoreoUtils'
import { paths } from '@/paths'
import { NAV_GRUPOS, NAV_ITEMS, type NavItem } from './navigation'
import { SaikiSessionProvider } from '@/features/saiki/SaikiSession'
const SaikiNotification = lazy(() => import('@/features/saiki/SaikiSensors').then(module => ({ default: module.SaikiNotification })))
const SaikiMini = lazy(() => import('@/features/saiki/SaikiMini').then(module => ({ default: module.SaikiMini })))

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const alertasAbiertas = useMonitoreoVivo()?.alertasAbiertas.length ?? 0
  const { empresa } = useEmpresa()
  const { cerrarSesion, rol, operario, proveedor } = useSession()
  const items = NAV_ITEMS.filter((i) => i.roles.includes(rol))
  const grupos = (Object.keys(NAV_GRUPOS) as NavItem['grupo'][]).filter((g) => items.some((i) => i.grupo === g))
  // Tarjeta de identidad: la empresa, o el operario / proveedor con la empresa a la que pertenece.
  const quien =
    rol === 'OPERARIO'
      ? { rotulo: 'Operario', nombre: operario ? `${operario.nombre} ${operario.apellido}` : '…', detalle: empresa?.nombre }
      : rol === 'PROVEEDOR'
        ? { rotulo: 'Proveedor', nombre: proveedor?.nombre ?? '…', detalle: empresa?.nombre }
        : { rotulo: 'Empresa', nombre: empresa?.nombre ?? '…', detalle: empresa?.ruc ? `RUC ${empresa.ruc}` : undefined }

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-fg">
      <div className="hazard-stripe h-1.5 shrink-0" aria-hidden="true" />
      <div className="px-5 pt-5 pb-4">
        <Brand />
        <div className="mt-5 rounded-md border border-white/8 bg-sidebar-2 px-3 py-2.5">
          <p className="font-mono text-[0.625rem] tracking-[0.16em] text-sidebar-muted uppercase">{quien.rotulo}</p>
          <p className="truncate text-sm font-medium" title={quien.nombre}>
            {quien.nombre}
          </p>
          {quien.detalle && <p className="truncate font-mono text-xs text-sidebar-muted">{quien.detalle}</p>}
        </div>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto px-3 pb-4">
        {grupos.map((g) => (
          <div key={g} className="mb-4">
            <p className="px-2 pb-1.5 font-mono text-[0.625rem] tracking-[0.16em] text-sidebar-muted uppercase">{NAV_GRUPOS[g]}</p>
            <ul className="flex flex-col gap-0.5">
              {items.filter((i) => i.grupo === g).map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end ?? false}
                    {...(onNavigate ? { onClick: onNavigate } : {})}
                    className={({ isActive }) =>
                      cn(
                        'group relative flex min-h-10 items-center gap-3 rounded-md px-3 text-sm transition-colors',
                        isActive
                          ? 'bg-sidebar-2 font-semibold text-white'
                          : 'text-sidebar-fg/80 hover:bg-sidebar-2/70 hover:text-white',
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <span
                          className={cn('absolute top-2 bottom-2 left-0 w-1 rounded-r bg-accent transition-opacity', isActive ? 'opacity-100' : 'opacity-0')}
                          aria-hidden="true"
                        />
                        <Icon name={item.icon} className={cn('size-[1.125rem]', isActive ? 'text-accent' : 'text-sidebar-muted group-hover:text-sidebar-fg')} />
                        <span>{item.label}{item.subtitle && <span className="block text-[10px] font-normal tracking-wide text-sidebar-muted">{item.subtitle}</span>}</span>
                        {item.to === paths.monitoreo && alertasAbiertas > 0 && (
                          <span className="ml-auto rounded-full bg-danger px-2 py-0.5 font-mono text-xs font-semibold text-white" aria-label={`${alertasAbiertas} alertas abiertas`}>
                            {alertasAbiertas}
                          </span>
                        )}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/8 p-3">
        <button
          type="button"
          onClick={cerrarSesion}
          className="flex min-h-10 w-full items-center gap-3 rounded-md px-3 text-sm text-sidebar-fg/80 hover:bg-sidebar-2 hover:text-white"
        >
          <Icon name="logout" className="size-[1.125rem] text-sidebar-muted" />
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}

/** Barra fina ámbar mientras se carga una ruta lazy. */
function NavigationProgress() {
  const navigation = useNavigation()
  if (navigation.state === 'idle') return null
  return (
    <div className="fixed inset-x-0 top-0 z-[70] h-0.5 overflow-hidden bg-accent/20" role="progressbar" aria-label="Cargando página">
      <div className="h-full w-1/3 animate-pulse bg-accent" />
    </div>
  )
}

export function AppLayout() {
  const toast = useToast()
  return (
    <SaikiSessionProvider><MonitoreoProvider
      onAlerta={(evento, alerta, d) => {
        if (evento === 'ABIERTA') toast.error(`${d?.nombre ?? 'Dispositivo'}: ${alerta.mensaje ?? alerta.titulo ?? ''}`.trim(), etiquetaAlerta(alerta.tipo_alerta))
      }}
    >
      <AppLayoutContenido />
    </MonitoreoProvider></SaikiSessionProvider>
  )
}

function AppLayoutContenido() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()
  const menuBtn = useRef<HTMLButtonElement>(null)
  const drawerRef = useRef<HTMLDivElement>(null)

  // Cierra el drawer al navegar.
  useEffect(() => setDrawerOpen(false), [location.pathname])

  // Esc para cerrar, bloqueo de scroll y foco inicial / de retorno.
  useEffect(() => {
    if (!drawerOpen) return
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    drawerRef.current?.querySelector<HTMLElement>('a, button')?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerOpen(false)
    }
    window.addEventListener('keydown', onKey)
    const btn = menuBtn.current
    return () => {
      document.body.style.overflow = prevOverflow
      window.removeEventListener('keydown', onKey)
      btn?.focus()
    }
  }, [drawerOpen])

  return (
    <div className="min-h-dvh bg-bg">
      <NavigationProgress />
      <Suspense fallback={null}><SaikiNotification /></Suspense>
      <Suspense fallback={null}><SaikiMini /></Suspense>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[80] focus:rounded focus:bg-surface focus:px-3 focus:py-2 focus:text-fg focus:shadow-pop"
      >
        Saltar al contenido
      </a>

      {/* Sidebar desktop */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <SidebarContent />
      </aside>

      {/* Barra superior móvil */}
      <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-white/8 bg-sidebar px-3 lg:hidden">
        <button
          ref={menuBtn}
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="flex size-10 items-center justify-center rounded-md text-sidebar-fg hover:bg-sidebar-2"
          aria-label="Abrir menú"
          aria-expanded={drawerOpen}
          aria-controls="drawer-navegacion"
        >
          <Icon name="menu" className="size-6" />
        </button>
        <Brand />
      </header>

      {/* Drawer móvil */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-overlay" onClick={() => setDrawerOpen(false)} aria-hidden="true" />
          <div
            id="drawer-navegacion"
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Menú de navegación"
            className="absolute inset-y-0 left-0 w-[min(18rem,85vw)] shadow-pop [animation:drawer-in_180ms_ease-out]"
          >
            <SidebarContent onNavigate={() => setDrawerOpen(false)} />
            <Button
              variant="ghost"
              size="sm"
              iconOnly
              icon="x"
              aria-label="Cerrar menú"
              onClick={() => setDrawerOpen(false)}
              className="absolute top-4 right-3 text-sidebar-fg hover:bg-sidebar-2 hover:text-white"
            />
          </div>
        </div>
      )}

      <main id="contenido" tabIndex={-1} className="outline-none lg:pl-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
