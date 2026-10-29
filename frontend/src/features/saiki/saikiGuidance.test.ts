import { describe, expect, it } from 'vitest'
import { cleanAnswer, requestsNavigation, speechText, suggestedGuide, voiceCommand } from './saikiGuidance'

describe('Saiki navigation and narration', () => {
  it('opens only known read-only screens after an explicit request', () => {
    expect(requestsNavigation('Abre mi inventario')).toBe(true)
    expect(suggestedGuide('Abre mi inventario')?.to).toBe('/inventario')
    expect(suggestedGuide('Muéstrame los gráficos de temperatura')?.to).toBe('/monitoreo')
    expect(requestsNavigation('¿Cómo está mi inventario?')).toBe(false)
    for (const [phrase, route] of [['quiero ver mi inventario', '/inventario'], ['llévame a sensores', '/monitoreo'], ['muéstrame los sensores', '/monitoreo'], ['abre la sección de productos', '/productos']]) {
      expect(requestsNavigation(phrase!)).toBe(true)
      expect(suggestedGuide(phrase!)?.to).toBe(route)
    }
    expect(suggestedGuide('abre https://evil.example')).toBeNull()
    expect(suggestedGuide('elimina todos los datos')).toBeNull()
  })
  it('handles explicit session commands without mistaking a normal question for a command', () => {
    expect(voiceCommand('Saiki, pausa.')).toBe('pause')
    expect(voiceCommand('Saiki, salir')).toBe('exit')
    expect(voiceCommand('¿Por qué se pausa el equipo de refrigeración?')).toBeNull()
  })
  it('never narrates model reasoning including an unterminated think block', () => {
    expect(cleanAnswer('<think>private</think>Resultado')).toBe('Resultado')
    expect(cleanAnswer('Resultado<think>private')).toBe('Resultado')
    expect(speechText('**Mira** [inventario](/inventario)')).toBe('Mira inventario')
  })
})
