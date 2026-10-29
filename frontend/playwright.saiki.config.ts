import { testBrowser } from './playwright.runtime'
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e', testMatch: ['saiki.spec.ts', 'abastecimiento.spec.ts', 'plano-reportes.spec.ts'], workers: 1, timeout: 30_000,
  use: { baseURL: 'http://localhost:15473', channel: testBrowser, headless: true, colorScheme: 'dark', screenshot: 'only-on-failure' },
  outputDir: '../artifacts/saiki-browser.local', reporter: 'list',
  webServer: process.env.SAIKI_TEST_EXTERNAL_SERVER ? undefined : {
    command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15473 --strictPort',
    url: 'http://localhost:15473', reuseExistingServer: false,
    env: { VITE_API_URL: '/api/v1' }, timeout: 60_000,
  },
})
