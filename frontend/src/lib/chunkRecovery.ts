const RETRY_KEY = 'psitwin:chunk-reload-at'
const RETRY_WINDOW_MS = 60_000

export function isChunkLoadError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : typeof error === 'string' ? error : ''
  return /failed to fetch dynamically imported module|error loading dynamically imported module|importing a module script failed|loading chunk .+ failed/i.test(message)
}

interface RecoveryOptions {
  storage: Pick<Storage, 'getItem' | 'setItem'>
  reload: () => void
  online: boolean
  now: number
}

export function recoverChunk(error: unknown, options: RecoveryOptions): boolean {
  if (!isChunkLoadError(error) || !options.online) return false
  try {
    const last = Number(options.storage.getItem(RETRY_KEY))
    if (last > 0 && options.now - last < RETRY_WINDOW_MS) return false
    // Persist before navigating so a permanently missing file cannot loop.
    options.storage.setItem(RETRY_KEY, String(options.now))
  } catch {
    // Without storage the route error still offers a manual retry.
    return false
  }
  options.reload()
  return true
}

export function installChunkRecovery(): void {
  window.addEventListener('vite:preloadError', (event) => {
    const error = (event as Event & { payload?: unknown }).payload
    let storage: Storage
    try { storage = window.sessionStorage } catch { return }
    const recovered = recoverChunk(error, {
      storage, reload: () => window.location.reload(),
      online: navigator.onLine, now: Date.now(),
    })
    if (recovered) event.preventDefault()
  })
}
