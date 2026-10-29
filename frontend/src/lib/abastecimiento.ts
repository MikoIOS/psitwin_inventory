/** Exact integer PEN cents for a quantity with at most three decimals. */
export function subtotalCentimos(quantity: string, cents: number): number | null {
  if (!/^\d+(?:[.,]\d{1,3})?$/.test(quantity.trim()) || !Number.isSafeInteger(cents) || cents <= 0) return null
  const [whole = '0', fraction = ''] = quantity.trim().replace(',', '.').split('.')
  const millis = BigInt(whole) * 1000n + BigInt(fraction.padEnd(3, '0'))
  const result = (millis * BigInt(cents) + 500n) / 1000n
  return result <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(result) : null
}
