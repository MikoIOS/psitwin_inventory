/**
 * Detalle de dispositivo (EMPRESA y OPERARIO): valores en vivo, gráfico por parámetro de las últimas horas
 * (`GET /dispositivos/{id}/lecturas`) y alertas con «Atender» (PATCH estado → VISTA).
 * EMPRESA: editar (nombre, rack, activo, límites), regenerar token (se muestra una vez) y eliminar.
 */
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { PARAMETROS, useAlertasSensores, useAtenderAlerta, useDeleteDispositivo, useLecturas, useRegenerarToken, type Alerta } from '@/api/dispositivos'
import { useUbicaciones } from '@/api/ubicaciones'
import { useRol } from '@/auth/useRol'
import { Button, Card, ConfirmDialog, DataTable, EmptyState, ErrorState, LoadingBlock, PageHeader, Select, StatusBadge, useApiErrorHandler, useToast } from '@/components/ui'
import { formatFechaHora, formatNumero } from '@/lib/format'
import { paths } from '@/paths'
import { DispositivoFormModal, TokenModal } from './DispositivoForm'
import { Grafico, type Punto } from './Grafico'
import { duracion, estadoDispositivo, ms, ETIQUETA_PARAMETRO, etiquetaAlerta, limiteEfectivo, UNIDAD, useAhora } from './monitoreoUtils'
import { BadgeEstadoSensor, IndicadorConexion, useDispositivosVivos, ValoresVivos } from './ValoresVivos'

const PERIODOS = [
  { value: '1', label: 'Última hora' },
  { value: '6', label: 'Últimas 6 horas' },
  { value: '24', label: 'Últimas 24 horas' },
  { value: '168', label: 'Últimos 7 días' },
]

export default function DispositivoDetallePage() {
  const { idDispositivo } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const { esEmpresa } = useRol()
  const ahora = useAhora()
  const { q, lista } = useDispositivosVivos()
  const ub = useUbicaciones()
  const [horas, setHoras] = useState(6)
  const lecturasQ = useLecturas(idDispositivo, horas)
  const historialQ = useAlertasSensores()
  const atender = useAtenderAlerta()
  const regenerar = useRegenerarToken()
  const eliminar = useDeleteDispositivo()
  const [editando, setEditando] = useState(false)
  const [confirmar, setConfirmar] = useState<'token' | 'eliminar' | null>(null)
  const [token, setToken] = useState<{ id: string; nombre: string; token: string } | null>(null)

  const back = { to: paths.monitoreo, label: 'Monitoreo' }
  const item = lista.find((x) => x.dispositivo.id_dispositivo === idDispositivo)
  if (q.isLoading) return <LoadingBlock label="Cargando dispositivo…" />
  if (q.error || !item)
    return (
      <>
        <PageHeader title="Dispositivo" back={back} />
        <ErrorState error={q.error ?? new Error('Dispositivo no encontrado')} onRetry={() => void q.refetch()} />
      </>
    )
  const { dispositivo: d, estado, rack } = item
  const est = d.activo ? estadoDispositivo(d, estado, ahora, rack) : 'sin_datos'
  const ubicacion = d.id_rack ? ub.porRack.get(d.id_rack)?.etiqueta : ub.zonas.find((z) => z.id_zona === d.id_zona)?.nombre

  // Alertas: las abiertas (en vivo) + el historial de la empresa, sin duplicar.
  const abiertas = estado?.alertas_abiertas ?? []
  const historial = (historialQ.data ?? []).filter((a) => a.id_dispositivo === d.id_dispositivo)
  const alertas = [...abiertas, ...historial.filter((h) => !abiertas.some((a) => a.id_alerta === h.id_alerta))].sort((a, b) =>
    (b.inicio ?? b.fecha_creacion ?? '').localeCompare(a.inicio ?? a.fecha_creacion ?? ''),
  )

  const serie = (p: (typeof PARAMETROS)[number] | 'puerta'): Punto[] =>
    (lecturasQ.data ?? []).flatMap((l) => {
      const v = p === 'puerta' ? (l.puerta == null ? null : l.puerta ? 1 : 0) : l[p]
      const t = ms(l.ts)
      return v == null || Number.isNaN(t) ? [] : [{ t, v }]
    })

  return (
    <>
      <PageHeader
        back={back}
        eyebrow={ubicacion ?? 'Dispositivo'}
        title={d.nombre}
        meta={
          <>
            <BadgeEstadoSensor estado={est} />
            <IndicadorConexion />
            {!d.activo && <StatusBadge estado="INACTIVO" />}
          </>
        }
        {...(esEmpresa
          ? {
              actions: (
                <>
                  <Button variant="secondary" icon="edit" onClick={() => setEditando(true)}>
                    Editar
                  </Button>
                  <Button variant="secondary" icon="key" onClick={() => setConfirmar('token')}>
                    Regenerar token
                  </Button>
                  <Button variant="ghost" icon="trash" className="hover:text-danger" onClick={() => setConfirmar('eliminar')}>
                    Eliminar
                  </Button>
                </>
              ),
            }
          : {})}
      />

      <div className="flex flex-col gap-5">
        <Card padding="md" title="Ahora" description={estado?.ultima_lectura ? `Última lectura ${formatFechaHora(new Date(ms(estado.ultima_lectura.ts)))}` : 'Aún no llegan lecturas de este dispositivo.'}>
          <ValoresVivos dispositivo={d} estado={estado} rack={rack} ahora={ahora} grande />
        </Card>

        <Card
          padding="md"
          title="Alertas"
          description={esEmpresa ? 'Una alerta por episodio. Se resuelven solas cuando el valor vuelve al rango.' : 'Alertas abiertas. Se resuelven solas cuando el valor vuelve al rango.'}
        >
          <DataTable<Alerta>
            caption="Alertas del dispositivo"
            data={alertas}
            loading={historialQ.isLoading}
            rowKey={(a) => a.id_alerta}
            empty={<EmptyState compact icon="check-circle" title="Sin alertas" description="Este dispositivo no tiene alertas." />}
            columns={[
              { id: 'tipo', header: 'Alerta', mobile: 'title', cell: (a) => etiquetaAlerta(a.tipo_alerta) },
              { id: 'estado', header: 'Estado', mobile: 'badge', cell: (a) => <StatusBadge estado={a.estado} /> },
              { id: 'inicio', header: 'Inicio', cell: (a) => formatFechaHora(new Date(ms(a.inicio ?? a.fecha_creacion))) },
              {
                id: 'duracion',
                header: 'Duración',
                cell: (a) => (a.duracion_s != null ? duracion(a.duracion_s) : a.inicio && !a.fin ? `${duracion((ahora - ms(a.inicio)) / 1000)} (en curso)` : '—'),
              },
              {
                id: 'valor',
                header: 'Valor / límite',
                cell: (a) => (a.valor_extremo ?? a.valor) != null ? `${formatNumero(a.valor_extremo ?? a.valor)}${a.limite != null ? ` (límite ${formatNumero(a.limite)})` : ''}` : '—',
              },
              { id: 'mensaje', header: 'Detalle', mobile: 'hidden', cell: (a) => a.mensaje ?? '—' },
            ]}
            actions={(a) =>
              a.estado === 'ACTIVA' || a.estado === 'ABIERTA' ? (
                <Button
                  size="sm"
                  icon="check"
                  loading={atender.isPending && atender.variables === a.id_alerta}
                  onClick={() =>
                    atender.mutate(a.id_alerta, {
                      onSuccess: () => toast.success('Alerta marcada como atendida.'),
                      onError: (e) => handleError(e, { title: 'No se pudo atender la alerta' }),
                    })
                  }
                >
                  Atender
                </Button>
              ) : null
            }
          />
        </Card>

        <Card
          padding="md"
          title="Historial"
          description="Línea punteada roja: límites configurados."
          actions={
            <Select
              aria-label="Periodo"
              placeholder={false}
              options={PERIODOS}
              value={String(horas)}
              onChange={(e) => setHoras(Number(e.target.value))}
            />
          }
        >
          {lecturasQ.isLoading ? (
            <LoadingBlock label="Cargando lecturas…" />
          ) : lecturasQ.error ? (
            <ErrorState error={lecturasQ.error} onRetry={() => void lecturasQ.refetch()} />
          ) : (
            <div className="grid gap-5 lg:grid-cols-2">
              {PARAMETROS.map((p) => {
                const lim = limiteEfectivo(d, p, rack)
                return (
                  <section key={p} aria-label={ETIQUETA_PARAMETRO[p]} data-testid={`grafico-${p}`}>
                    <h3 className="mb-1 text-sm font-medium text-fg">
                      {ETIQUETA_PARAMETRO[p]} <span className="text-fg-subtle">({UNIDAD[p]})</span>
                    </h3>
                    <Grafico puntos={serie(p)} min={lim.min} max={lim.max} unidad={UNIDAD[p]} titulo={`${ETIQUETA_PARAMETRO[p]} en el tiempo`} />
                  </section>
                )
              })}
              <section aria-label="Puerta" data-testid="grafico-puerta">
                <h3 className="mb-1 text-sm font-medium text-fg">Puerta</h3>
                <Grafico puntos={serie('puerta')} unidad="" escalon titulo="Puerta abierta o cerrada en el tiempo" />
              </section>
            </div>
          )}
        </Card>
      </div>

      <DispositivoFormModal open={editando} onClose={() => setEditando(false)} dispositivo={d} />
      <TokenModal datos={token} onClose={() => setToken(null)} />
      <ConfirmDialog
        open={confirmar === 'token'}
        title="Regenerar token"
        description="El token actual dejará de funcionar: tendrás que cargar el nuevo en el ESP32."
        confirmLabel="Regenerar"
        tone="primary"
        loading={regenerar.isPending}
        onCancel={() => setConfirmar(null)}
        onConfirm={() =>
          regenerar.mutate(d.id_dispositivo, {
            onSuccess: (r) => {
              setConfirmar(null)
              setToken({ id: d.id_dispositivo, nombre: d.nombre, token: r.token })
            },
            onError: (e) => {
              setConfirmar(null)
              handleError(e, { title: 'No se pudo regenerar el token' })
            },
          })
        }
      />
      <ConfirmDialog
        open={confirmar === 'eliminar'}
        title="Eliminar dispositivo"
        description={`Se eliminará «${d.nombre}». Sus mensajes MQTT dejarán de aceptarse.`}
        confirmLabel="Eliminar"
        tone="danger"
        loading={eliminar.isPending}
        onCancel={() => setConfirmar(null)}
        onConfirm={() =>
          eliminar.mutate(d.id_dispositivo, {
            onSuccess: () => {
              toast.success('Dispositivo eliminado')
              navigate(paths.monitoreo, { replace: true })
            },
            onError: (e) => {
              setConfirmar(null)
              handleError(e, { title: 'No se pudo eliminar el dispositivo' })
            },
          })
        }
      />
    </>
  )
}
