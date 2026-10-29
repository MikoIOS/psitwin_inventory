import { WarehouseMapSelector } from '@/features/almacenes/WarehouseMap'
/**
 * Monitoreo (EMPRESA y OPERARIO; el operario ve solo su almacén): tarjetas por dispositivo agrupadas por zona, con
 * valores en vivo (WebSocket) y color según estado (normal / fuera de rango / alerta / sin datos).
 * EMPRESA: «Nuevo dispositivo» (el token se muestra una vez).
 */
import { useState } from 'react'
import { Link } from 'react-router'
import { useZonas } from '@/api/zonas'
import { useRol } from '@/auth/useRol'
import { Button, EmptyState, ErrorState, LoadingBlock, PageHeader } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFechaHora } from '@/lib/format'
import { paths } from '@/paths'
import { DispositivoFormModal, TokenModal } from './DispositivoForm'
import { RackMonitor } from './RackMonitor'
import { ESTADO_SENSOR, estadoDispositivo, etiquetaAlerta, ms, useAhora } from './monitoreoUtils'
import { BadgeEstadoSensor, IndicadorConexion, useDispositivosVivos, ValoresVivos } from './ValoresVivos'

export default function MonitoreoPage() {
  const { esEmpresa } = useRol()
  const ahora = useAhora()
  const { q, lista } = useDispositivosVivos()
  const zonas = new Map((useZonas().data ?? []).map((z) => [z.id_zona, z]))
  const [creando, setCreando] = useState(false)
  const [token, setToken] = useState<{ id: string; nombre: string; token: string } | null>(null)

  const porZona = new Map<string, typeof lista>()
  for (const item of lista) porZona.set(item.dispositivo.id_zona, [...(porZona.get(item.dispositivo.id_zona) ?? []), item])
  const grupos = [...porZona.entries()].sort(([a], [b]) => (zonas.get(a)?.nombre ?? '').localeCompare(zonas.get(b)?.nombre ?? '', 'es', { numeric: true }))

  return (
    <>
      <PageHeader
        eyebrow="Sensores"
        title="Monitoreo"
        description="Temperatura, puerta, ambiente y corriente de cada equipo de frío, en tiempo real."
        meta={<IndicadorConexion />}
        {...(esEmpresa
          ? {
              actions: (
                <Button icon="plus" onClick={() => setCreando(true)}>
                  Nuevo dispositivo
                </Button>
              ),
            }
          : {})}
      />

      <RackMonitor />
      <WarehouseMapSelector />
      {q.isLoading ? (
        <LoadingBlock label="Cargando dispositivos…" />
      ) : q.error ? (
        <ErrorState error={q.error} onRetry={() => void q.refetch()} />
      ) : lista.length === 0 ? (
        <EmptyState
          icon="snowflake"
          title="Aún no hay dispositivos"
          description={esEmpresa ? 'Registra un ESP32 por equipo de frío para ver sus lecturas aquí.' : 'La empresa aún no registró sensores en tu almacén.'}
          {...(esEmpresa
            ? {
                action: (
                  <Button icon="plus" onClick={() => setCreando(true)}>
                    Nuevo dispositivo
                  </Button>
                ),
              }
            : {})}
        />
      ) : (
        <div className="flex flex-col gap-6">
          {grupos.map(([idZona, items]) => (
            <section key={idZona} aria-labelledby={`zona-${idZona}`}>
              <h2 id={`zona-${idZona}`} className="label-stencil mb-3">
                {zonas.get(idZona)?.nombre ?? 'Zona'}
                {zonas.get(idZona)?.refrigerada && ' · refrigerada'}
              </h2>
              <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {items.map(({ dispositivo: d, estado, rack }) => {
                  const est = d.activo ? estadoDispositivo(d, estado, ahora, rack) : 'sin_datos'
                  const alertas = estado?.alertas_abiertas ?? []
                  return (
                    <li key={d.id_dispositivo}>
                      <Link
                        to={paths.dispositivo(d.id_dispositivo)}
                        data-testid="tarjeta-dispositivo"
                        data-estado={est}
                        className={cn(
                          'flex h-full flex-col gap-3 rounded-[calc(var(--radius-ui)+2px)] border-2 bg-surface p-4 shadow-card transition-shadow hover:shadow-pop',
                          ESTADO_SENSOR[est].borde,
                        )}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="truncate font-semibold text-fg">{d.nombre}</p>
                            <p className="truncate text-xs text-fg-muted">
                              {rack ? `Rack ${rack.codigo}` : 'Sin rack'}
                              {!d.activo && ' · inactivo'}
                            </p>
                          </div>
                          <BadgeEstadoSensor estado={est} />
                        </div>
                        <ValoresVivos dispositivo={d} estado={estado} rack={rack} ahora={ahora} />
                        {alertas.length > 0 && (
                          <ul
                            aria-label={`Alertas de ${d.nombre}`}
                            className="flex max-h-32 flex-col gap-1 overflow-y-auto overscroll-contain border-t border-border pt-2 pr-2 text-xs text-danger [scrollbar-gutter:stable]"
                          >
                            {alertas.map((a) => (
                              <li key={a.id_alerta}>● {etiquetaAlerta(a.tipo_alerta)}</li>
                            ))}
                          </ul>
                        )}
                        <p className="mt-auto text-[0.6875rem] text-fg-subtle">
                          Última lectura: {estado?.ultima_lectura ? formatFechaHora(new Date(ms(estado.ultima_lectura.ts))) : '—'}
                        </p>
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </section>
          ))}
        </div>
      )}

      <DispositivoFormModal
        open={creando}
        onClose={() => setCreando(false)}
        dispositivo={null}
        onCreado={(d) => setToken({ id: d.id_dispositivo, nombre: d.nombre, token: d.token })}
      />
      <TokenModal datos={token} onClose={() => setToken(null)} />
    </>
  )
}
