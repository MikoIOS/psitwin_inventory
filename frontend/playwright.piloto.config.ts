import { testBrowser, testNpm, testPython } from './playwright.runtime'
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e/piloto', workers: 1, timeout: 120_000,
  testMatch: '**/tienda.spec.ts',
  projects: [{ name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } }, { name: 'mobile', use: { viewport: { width: 390, height: 844 }, isMobile: true } }],
  use: { baseURL: 'http://localhost:15174', channel: testBrowser, headless: true, screenshot: 'only-on-failure' },
  outputDir: '../artifacts/piloto.local/browser',
  reporter: [['list'], ['json', { outputFile: '../artifacts/piloto.local/browser.json' }]],
  webServer: [
    { command: `${testPython} -m uvicorn tests.pilot_browser_app:app --app-dir ../backend --host 127.0.0.1 --port 18081`, url: 'http://127.0.0.1:18081/health', env: { PSITWIN_PILOT_BROWSER: '1' }, timeout: 60000 },
    { command: `${testNpm} run dev -- --host 127.0.0.1 --port 15174 --strictPort`, url: 'http://localhost:15174', env: { VITE_PROXY_TARGET: 'http://127.0.0.1:18081', VITE_API_URL: '/api/v1' }, timeout: 60000 },
  ],
})
