import { existsSync } from 'node:fs'

const windows = process.platform === 'win32'
const defaultPython = windows ? '..\\.runtime.local\\python\\python.exe'
  : existsSync('../.venv/bin/python') ? '../.venv/bin/python' : 'python3'
const python = process.env.PSITWIN_TEST_PYTHON || defaultPython
const quote = (value: string) => windows ? `"${value.replaceAll('"', '""')}"`
  : `'${value.replaceAll("'", "'\\''")}'`

export const testPython = quote(python)
export const testNpm = windows ? 'npm.cmd' : 'npm'
// Use Playwright's Chromium on Linux; optionally choose an installed channel.
export const testBrowser = process.env.PSITWIN_TEST_BROWSER || (windows ? 'msedge' : 'chromium')
