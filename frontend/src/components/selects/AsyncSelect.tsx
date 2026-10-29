/**
 * Base de los selects conectados a datos.
 *
 * Detalle importante con react-hook-form + <select> nativo: si el <select> se monta ANTES de
 * tener opciones, el valor por defecto se pierde en el DOM. Por eso el <select> real (el que
 * recibe el `ref` de `register`) solo se monta cuando hay opciones; mientras tanto se muestra
 * un placeholder deshabilitado. `resetKey` fuerza el remontaje cuando cambia la dependencia
 * (ej. el almacén en ZonaSelect) para que RHF vuelva a aplicar el valor.
 */
import { ApiError } from '@/api/client'
import { Select, type SelectOption, type SelectProps } from '@/components/ui/Select'

export interface AsyncSelectProps extends Omit<SelectProps, 'options'> {
  options: SelectOption[] | undefined
  loading?: boolean
  error?: unknown
  /** Si se define, el select se muestra deshabilitado con este texto (ej. "Primero elige un almacén"). */
  blockedReason?: string | undefined
  /** Texto cuando no hay opciones. */
  emptyText?: string
  resetKey?: string | undefined
}

export function AsyncSelect({
  options,
  loading,
  error,
  blockedReason,
  emptyText = 'No hay opciones disponibles',
  resetKey,
  placeholder = 'Selecciona…',
  ref,
  ...props
}: AsyncSelectProps) {
  const { onChange: _onChange, onBlur: _onBlur, value: _value, defaultValue: _dv, ...visual } = props
  const stub = (texto: string) => <Select {...visual} disabled placeholder={texto} aria-busy={loading || undefined} />

  if (blockedReason) return stub(blockedReason)
  if (loading && !options) return stub('Cargando…')
  if (error && !options?.length) return stub(error instanceof ApiError ? `Error: ${error.detail}` : 'Error al cargar')
  if (!options || options.length === 0) return stub(emptyText)

  return <>{error ? <p role="alert" className="text-sm text-danger">No se pudieron actualizar las opciones. Se muestran los últimos datos cargados.</p> : null}<Select key={resetKey ?? 'default'} ref={ref} {...props} options={options} placeholder={placeholder} /></>
}
