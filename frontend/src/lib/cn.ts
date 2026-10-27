/** Une clases condicionalmente: cn('a', cond && 'b', undefined) → "a b". Ignora todo lo que no sea string no vacío. */
export function cn(...parts: (string | boolean | number | bigint | null | undefined)[]): string {
  return parts.filter((p): p is string => typeof p === 'string' && p !== '').join(' ')
}
