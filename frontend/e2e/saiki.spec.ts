import { test, expect, type Page } from '@playwright/test'

// Isolated fixtures: all API and speech calls are mocked; no production writes.
const company = { id_empresa: 'saiki-test', nombre: 'Empresa de prueba', correo: 'test@example.test' }
async function setup(page: Page, failData = false, withData = false, mockSynthesis = true, localCapture = false) {
  const questions: Record<string, unknown>[] = []
  await page.addInitScript(({ company, mockSynthesis, localCapture }) => {
    if (!localCapture) Object.defineProperty(window, 'MediaRecorder', { configurable: true, value: undefined })
    localStorage.setItem('psitwin.token', 'isolated-browser-test')
    localStorage.setItem('psitwin.sesion', JSON.stringify({ rol: 'EMPRESA', empresa: company }))
    const state = (window as any).__saikiTest = { recognitions: [], spoken: [], active: 0, maxActive: 0 }
    class Recognition {
      running = false
      onstart: any; onend: any; onerror: any; onresult: any
      constructor() { state.recognitions.push(this) }
      start() { this.running = true; state.active++; state.maxActive = Math.max(state.active, state.maxActive); this.onstart?.() }
      abort() { if (this.running) state.active--; this.running = false; this.onend?.() }
      stop() { this.abort() }
    }
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: Recognition })
    if (mockSynthesis) {
      Object.defineProperty(window, 'SpeechSynthesisUtterance', { configurable: true, value: class { constructor(public text: string) {} } })
      Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
      getVoices: () => [{ voiceURI: 'test-jorge', name: 'Microsoft Jorge', lang: 'es-MX' }],
      addEventListener() {}, removeEventListener() {},
      speak(utterance: any) { state.spoken.push(utterance.text); state.utterance = utterance; utterance.onstart?.() },
      cancel() { state.utterance = null },
      } })
    }
    Object.defineProperty(window, 'WebSocket', { configurable: true, value: class {
      close() {} send() {} addEventListener() {} removeEventListener() {}
    } })
  }, { company, mockSynthesis, localCapture })
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    if (path === '/saiki/events') {
      const body = route.request().postDataJSON()
      questions.push(body)
      return route.fulfill({ contentType: 'application/x-ndjson', body: JSON.stringify({ type: 'result', result: { answer: `Respuesta verificada: ${body.question}`, model: 'mock', warnings: [] } }) + '\n' })
    }
    if (failData && ['/dispositivos', '/alertas', '/productos'].includes(path))
      return route.fulfill({ status: 503, json: { detail: 'Controlled unavailable service' } })
    const data = withData && path === '/productos' ? [{ id_producto: 'p1', nombre: 'Producto de prueba' }]
      : withData && path.startsWith('/detalles-inventario/producto/') ? [{ id_inventario: 'i1', id_producto: 'p1', id_rack: 'r1', stock_actual: 10 }]
      : withData && path.includes('/zonas') ? [{ id_zona: 'z1', id_almacen: 'w1', nombre: 'Zona de prueba' }]
      : withData && path.includes('/racks') ? [{ id_rack: 'r1', id_zona: 'z1', codigo: 'R1', nivel: 1 }]
      : withData && path === '/dispositivos' ? [{ id_dispositivo: 'd1', nombre: 'Equipo de prueba', id_almacen: 'w1', id_zona: 'z1', activo: true, parametros_disponibles: ['t_int'] }]
      : withData && path.includes('/lecturas') ? { puntos: [{ ts: new Date().toISOString(), t_int: 4 }] }
      : path === '/auth/me' ? { rol: 'EMPRESA', empresa: company }
      : path === '/empresas/me' ? company
      : path.includes('/almacenes') ? [{ id_almacen: 'w1', id_empresa: company.id_empresa, nombre: 'Almacén de prueba' }]
      : path === '/saiki/health' ? { ready: true, model: 'mock' }
      : []
    await route.fulfill({ json: data })
  })
  await page.goto('/saiki')
  await expect(page.getByRole('heading', { name: 'Conversación', exact: true })).toBeVisible()
  return questions
}
async function say(page: Page, transcript: string, final = true) {
  await page.evaluate(({ transcript, final }) => {
    const state = (window as any).__saikiTest
    const recognition = state.recognitions.at(-1)
    recognition.onresult?.({ resultIndex: 0, results: { length: 1, 0: { isFinal: final, 0: { transcript } } } })
  }, { transcript, final })
}
async function endSpeech(page: Page) {
  // One response can be chunked. End each queued utterance until playback stops.
  for (let i = 0; i < 10; i++) {
    const playing = await page.evaluate(() => !!(window as any).__saikiTest.utterance)
    if (!playing) break
    await page.evaluate(() => {
      const state = (window as any).__saikiTest
      const utterance = state.utterance; state.utterance = null; utterance?.onend?.()
    })
  }
}

test('spoken Spanish appears once, answers are spoken, session survives guided routes and mini controls', async ({ page }) => {
  const questions = await setup(page)
  await page.getByRole('button', { name: 'Iniciar conversación por voz' }).click()
  await expect(page.getByRole('button', { name: 'Enviar grabación', exact: true })).toHaveCount(0)
  await expect(page.getByText(/La sesión sigue abierta hasta que salgas/)).toHaveCount(0)
  await say(page, 'abre inventario', false)
  await expect(page).toHaveURL(/\/saiki$/)
  expect(questions).toHaveLength(0)
  await say(page, 'abre inventario')
  await say(page, 'abre inventario')
  await expect(page).toHaveURL(/\/inventario$/)
  const mini = page.getByRole('complementary', { name: 'Saiki, conversación de voz activa' })
  await expect(mini).toBeVisible()
  await expect(mini.getByRole('log')).toContainText('Tú: abre inventario')
  await expect(mini.getByRole('log')).toContainText('Saiki: Respuesta verificada')
  expect(questions).toHaveLength(1)
  expect(await page.evaluate(() => (window as any).__saikiTest.active)).toBe(0)
  await endSpeech(page)
  await expect.poll(() => page.evaluate(() => (window as any).__saikiTest.active)).toBe(1)
  await say(page, 'muéstrame los sensores')
  await expect(page).toHaveURL(/\/monitoreo$/)
  expect(questions[1]?.history).toEqual([{ role: 'user', content: 'abre inventario' }, { role: 'assistant', content: 'Respuesta verificada: abre inventario' }])
  await mini.getByRole('button', { name: 'Minimizar', exact: true }).click()
  await expect(mini.getByRole('log')).toHaveCount(0)
  await mini.getByRole('button', { name: 'Mostrar', exact: true }).click()
  await expect(mini.getByRole('log')).toBeVisible()
  await mini.getByRole('button', { name: 'Ampliar', exact: true }).click()
  await expect(page).toHaveURL(/\/saiki$/)
  await expect(page.getByText('muéstrame los sensores', { exact: true })).toBeVisible()
  expect(await page.evaluate(() => (window as any).__saikiTest.maxActive)).toBe(1)
  expect(await page.evaluate(() => (window as any).__saikiTest.spoken.length)).toBeGreaterThan(0)
  await page.getByRole('button', { name: 'Salir de la voz', exact: true }).click()
  await expect(mini).toHaveCount(0)
  await page.reload()
  await expect(page.getByText('abre inventario', { exact: true })).toBeVisible()
})

test('typed conversation speaks without activating microphone and has no speed slider', async ({ page }) => {
  const questions = await setup(page)
  await expect(page.getByRole('slider', { name: 'Velocidad de habla' })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Voz de Saiki', exact: true })).toHaveCount(0)
  await expect(page.getByRole('combobox', { name: 'Voz', exact: true })).toHaveCount(0)
  await page.getByRole('textbox', { name: 'Pregunta para Saiki' }).fill('Explica mi inventario')
  await page.getByRole('button', { name: 'Enviar', exact: true }).click()
  await expect(page.getByText('Respuesta verificada: Explica mi inventario', { exact: true })).toBeVisible()
  expect(questions).toHaveLength(1)
  expect(await page.evaluate(() => (window as any).__saikiTest.spoken)).toEqual(['Respuesta verificada: Explica mi inventario'])
  expect(await page.evaluate(() => (window as any).__saikiTest.recognitions.length)).toBe(0)
})

test('empty data is distinct from technical errors', async ({ page }) => {
  await setup(page)
  await expect(page.getByText('Sin datos disponibles. Todavía no hay equipos registrados.')).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Producto', exact: true })).toContainText('No hay productos')
  await expect(page.getByRole('combobox', { name: 'Inventario', exact: true })).toContainText('Primero elige un producto')
  await page.getByText('Historial de incidentes (0)', { exact: true }).click()
  await expect(page.getByText('No hay incidentes registrados disponibles.')).toBeVisible()
})

test('failed data requests show errors instead of claiming there are no records', async ({ page }) => {
  await setup(page, true)
  await expect(page.getByText('No se pudo consultar los equipos. Revisa la conexión.')).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Sin datos disponibles. Todavía no hay equipos registrados.')).toHaveCount(0)
  await expect(page.getByText('Historial de incidentes no disponible')).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Producto', exact: true })).toContainText('Error:')
})

test('permission denial pauses voice without losing written history', async ({ page }) => {
  await setup(page)
  await page.getByRole('textbox', { name: 'Pregunta para Saiki' }).fill('Hola Saiki')
  await page.getByRole('button', { name: 'Enviar', exact: true }).click()
  await expect(page.getByText('Respuesta verificada: Hola Saiki', { exact: true })).toBeVisible()
  await endSpeech(page)
  await page.getByRole('button', { name: 'Iniciar conversación por voz' }).click()
  await page.evaluate(() => (window as any).__saikiTest.recognitions.at(-1).onerror?.({ error: 'not-allowed' }))
  await expect(page.getByRole('alert').filter({ hasText: 'El micrófono no tiene permiso' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Reanudar', exact: true })).toBeVisible()
  await expect(page.getByText('Hola Saiki', { exact: true })).toBeVisible()
  expect(await page.evaluate(() => (window as any).__saikiTest.active)).toBe(0)
})

test('selected product, inventory, sensor and period reach Saiki', async ({ page }) => {
  const questions = await setup(page, false, true)
  await page.getByRole('combobox', { name: 'Producto', exact: true }).selectOption('p1')
  await page.getByRole('combobox', { name: 'Inventario', exact: true }).selectOption('i1')
  await page.getByRole('combobox', { name: 'Equipo', exact: true }).selectOption('d1')
  await page.getByRole('combobox', { name: 'Periodo', exact: true }).selectOption('6')
  await page.getByRole('button', { name: 'Saiki, explícame este equipo', exact: true }).click()
  await expect.poll(() => questions.length).toBe(1)
  expect(questions[0]).toMatchObject({ id_producto: 'p1', id_inventario: 'i1', id_dispositivo: 'd1', sensor_horas: 6 })
})

test('native Edge voice catalogue is inspected without speech mocks', async ({ page }, info) => {
  await setup(page, false, false, false)
  const voices = await page.evaluate(async () => {
    if (!window.speechSynthesis) return []
    if (!speechSynthesis.getVoices().length) await new Promise<void>(resolve => {
      speechSynthesis.addEventListener('voiceschanged', () => resolve(), { once: true })
      setTimeout(resolve, 3000)
    })
    return speechSynthesis.getVoices().map(v => ({ name: v.name, lang: v.lang, localService: v.localService }))
  })
  await info.attach('native-voices.json', { body: JSON.stringify(voices, null, 2), contentType: 'application/json' })
  console.log('Voces españolas nativas de Edge:', voices.filter(v => /^es/i.test(v.lang)))
  test.skip(!voices.length, 'Este navegador de pruebas no expone voces nativas; comprobar audio manualmente.')
  expect(voices.every(v => v.name && v.lang)).toBe(true)
  let localRequests = 0
  // Real browser synthesizer, deterministic local audio fixture on recovery.
  await page.route('**/api/v1/saiki/voice/synthesize', route => {
    localRequests++
    expect(route.request().postDataJSON().voice).toBe('em_alex')
    return route.fulfill({ path: '../artifacts/saiki-em_santa.wav', contentType: 'audio/wav' })
  })
  await page.evaluate(() => {
    const state = (window as any).__nativeSpeech = { started: 0, errors: [] as string[], calls: [] as string[] }
    const speak = speechSynthesis.speak.bind(speechSynthesis)
    speechSynthesis.speak = utterance => {
      state.calls.push(utterance.text)
      utterance.addEventListener('start', () => state.started++)
      utterance.addEventListener('error', event => state.errors.push(event.error))
      speak(utterance)
    }
  })
  await page.getByRole('textbox', { name: 'Pregunta para Saiki' }).fill('Hola Saiki')
  await page.getByRole('button', { name: 'Enviar', exact: true }).click()
  await expect(page.getByText('Respuesta verificada: Hola Saiki', { exact: true })).toBeVisible()
  await expect.poll(() => page.evaluate(() => (window as any).__nativeSpeech.calls.length)).toBeGreaterThan(0)
  await expect.poll(async () => localRequests > 0 || await page.evaluate(() => (window as any).__nativeSpeech.started > 0), { timeout: 15000 }).toBe(true)
  if (localRequests) {
    await expect(page.getByText('Voz disponible: Kokoro em_alex')).toBeVisible()
    await expect(page.locator('.saiki-presence[data-state="speaking"]')).toBeVisible()
  }

})


test('local capture detects quiet speech, transcribes and continues without browser STT', async ({ page }) => {
  await page.addInitScript(() => {
    const mic = (window as any).__localMic = { opened: 0, stopped: 0, level: .01 }
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: {
      getUserMedia: async () => { mic.opened++; return { getTracks: () => [{ stop: () => mic.stopped++ }] } },
    } })
    Object.defineProperty(window, 'AudioContext', { configurable: true, value: class {
      state = 'running'; resume = async () => {}; close = async () => {}
      createMediaStreamSource() { return { connect() {} } }
      createAnalyser() { return { fftSize: 2048, getFloatTimeDomainData(samples: Float32Array) { samples.fill(mic.level) } } }
    } })
    Object.defineProperty(window, 'MediaRecorder', { configurable: true, value: class {
      static isTypeSupported() { return true }
      state = 'inactive'; mimeType = 'audio/webm'; onstop: any; ondataavailable: any
      start() { this.state = 'recording' }
      stop() { if (this.state !== 'recording') return; this.state = 'inactive'; this.ondataavailable?.({ data: new Blob([new Uint8Array(200)]) }); this.onstop?.() }
    } })
  })
  const questions = await setup(page, false, false, true, true)
  let transcripts = 0
  await page.route('**/api/v1/saiki/voice/transcribe', route => { transcripts++; return route.fulfill({ json: { text: 'Revisa mis sensores' } }) })
  await page.getByRole('button', { name: 'Iniciar conversación por voz' }).click()
  await expect.poll(() => page.evaluate(() => (window as any).__localMic.opened)).toBe(1)
  await expect(page.getByText('Recibiendo sonido', { exact: true })).toBeVisible()
  await page.waitForTimeout(300)
  await page.evaluate(() => { (window as any).__localMic.level = 0 })
  await expect(page.getByText('Revisa mis sensores', { exact: true })).toBeVisible()
  await expect(page.getByText('Respuesta verificada: Revisa mis sensores', { exact: true })).toBeVisible()
  expect(transcripts).toBe(1)
  expect(questions).toHaveLength(1)
  await expect.poll(() => page.evaluate(() => (window as any).__localMic.stopped)).toBe(1)
  await endSpeech(page)
  await expect.poll(() => page.evaluate(() => (window as any).__localMic.opened)).toBe(2)
})
