import { defineConfig } from '@playwright/test'
import base from './playwright.piloto.config'
export default defineConfig({
  ...base,
  testMatch: '**/inventario.spec.ts',
  outputDir: '../artifacts/inventario-corregido.local/browser',
  reporter: [['list'], ['json', { outputFile: '../artifacts/inventario-corregido.local/resultados.json' }]],
  webServer: base.webServer!.map(server => ({ ...server, env: { ...server.env, PSITWIN_INVENTORY_WRITE_TESTS: '1' } })),
})
