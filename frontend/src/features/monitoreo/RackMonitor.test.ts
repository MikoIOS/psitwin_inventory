import { describe, expect, it } from 'vitest'
import { camposDisponibles } from './RackMonitor'
import { estadoParametro } from './monitoreoUtils'
import type { Dispositivo, EstadoDispositivo } from '@/api/dispositivos'

const device: Dispositivo = { id_dispositivo: 'sensor', id_almacen: 'a', id_zona: 'z', id_rack: 'r', nombre: 'Sensor', activo: true, limites: {} }
describe('sensor capability and freshness', () => {
  it('does not invent sensor types from default thresholds', () => {
    expect(camposDisponibles({ ...device, limites_efectivos: { t_int: { min: 0, max: 6 } } })).toEqual([])
    expect(camposDisponibles({ ...device, parametros_disponibles: ['t_int', 'hum'] })).toEqual(['t_int', 'hum'])
  })
  it('never presents a missing parameter as normal even when another sensor is fresh', () => {
    const now = Date.now()
    const state: EstadoDispositivo = { conectado: true, ultima_lectura: { ts: new Date(now).toISOString(), t_int: 4 }, puerta_abierta_desde: null, alertas_abiertas: [] }
    expect(estadoParametro(device, state, 'hum', now)).toBe('sin_datos')
    expect(estadoParametro(device, state, 't_int', now)).toBe('normal')
    expect(estadoParametro(device, state, 't_int', now + 6000)).toBe('sin_datos')
  })
})
