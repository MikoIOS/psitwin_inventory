import { testBrowser, testNpm, testPython } from './playwright.runtime'
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/auth.spec.ts',
  workers: 1,
  projects: [
    { name: 'desktop', use: { viewport: { width: 1280, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, colorScheme: 'dark' } },
  ],
  timeout: 60_000,
  use: { baseURL: 'http://localhost:15173', channel: testBrowser, headless: true, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  outputDir: '../artifacts/auth-browser.local/results',
  reporter: [['list'], ['json', { outputFile: '../artifacts/auth-browser.local/results.json' }]],
  webServer: [
    {
      command: `${testPython} -m uvicorn tests.browser_auth_app:app --app-dir ../backend --host 127.0.0.1 --port 18080`,
      url: 'http://127.0.0.1:18080/__test/status',
      reuseExistingServer: false,
      timeout: 60_000,
      env: { PSITWIN_BROWSER_TEST: '1', SECRET_KEY: 'browser-test-signing-key-not-used-in-production', GOOGLE_CLIENT_ID: '', GOOGLE_CLIENT_SECRET: '', FRONTEND_URL: 'http://localhost:15173', EMAIL_ENABLED: 'true', SMTP_USER: 'psitwin2026@gmail.com', SMTP_APP_PASSWORD: 'browser-test-only', MQTT_ENABLED: 'false' },
    },
    {
      command: `${testNpm} run dev -- --host 127.0.0.1 --port 15173 --strictPort`,
      url: 'http://localhost:15173/registro',
      reuseExistingServer: false,
      env: { VITE_PROXY_TARGET: 'http://127.0.0.1:18080', VITE_API_URL: '/api/v1' },
      timeout: 60_000,
    },
  ],
})
