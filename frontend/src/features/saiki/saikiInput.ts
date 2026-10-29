/** Reject only obvious silence/noise. Unknown topics and short valid questions remain valid. */
export function intelligibleInput(text: string): boolean {
  const value = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase()
  if (!/[a-z]/i.test(value)) return false
  const words = value.replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean)
  if (!words.length || words.every(w => /^(?:eh+|ah+|uh+|em+|mmm+|hmm+|ruido|silencio|inaudible)$/.test(w))) return false
  if (/^(?:asdf|qwerty|zxcv|aaaaa|eeee+|zzzzz)+$/.test(value.replace(/\s/g, ''))) return false
  return true
}
