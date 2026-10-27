/**
 * Manejo uniforme de errores de API en formularios y acciones.
 *
 *   const handleError = useApiErrorHandler()
 *   create.mutate(body, {
 *     onSuccess: () => toast.success('Guardado'),
 *     onError: (err) => handleError(err, { form }),   // 422 → campos; 409/404/500 → toast
 *   })
 *
 * Reglas:
 *  - 422: `applyFieldErrors` pinta los errores en los campos del form (FastAPI detail[].loc).
 *         Los que no correspondan a ningún campo se muestran en un toast.
 *  - 409: toast con el `detail` del backend (regla de negocio: stock insuficiente, etc.).
 *  - 404: toast con el detail o "No se encontró el registro".
 *  - 401: el cliente ya limpia la sesión y redirige a /login (no se muestra nada aquí).
 *  - 403: toast "Acceso denegado" con el detail (la sesión NO se cierra).
 *  - 0 (red) / 5xx: mensaje genérico (el cliente ya hace console.error en 5xx).
 */
import { useCallback } from 'react'
import type { FieldValues, Path, UseFormGetValues, UseFormSetError } from 'react-hook-form'
import { ApiError } from '@/api/client'
import { useToast } from './Toast'

/** Subconjunto de UseFormReturn necesario (acepta el resultado de useForm directamente). */
export interface FormLike<T extends FieldValues> {
  setError: UseFormSetError<T>
  getValues: UseFormGetValues<T>
}

export interface ApplyResult {
  /** Campos a los que se asignó error. */
  applied: string[]
  /** Errores sin campo correspondiente en el form. */
  unmatched: Record<string, string>
}

/**
 * Aplica los errores 422 de un ApiError a un formulario react-hook-form.
 * Opcional `fieldMap` para renombrar campos del backend → form (ej. { id_rack: 'rack' }).
 */
export function applyFieldErrors<T extends FieldValues>(
  form: FormLike<T>,
  error: unknown,
  fieldMap: Record<string, string> = {},
): ApplyResult {
  const result: ApplyResult = { applied: [], unmatched: {} }
  if (!(error instanceof ApiError) || !error.hasFieldErrors) return result
  const values = (form.getValues() ?? {}) as Record<string, unknown>
  let first = true
  for (const [campoBackend, msg] of Object.entries(error.fieldErrors)) {
    const campo = fieldMap[campoBackend] ?? campoBackend
    if (campo in values) {
      form.setError(campo as Path<T>, { type: 'server', message: msg }, { shouldFocus: first })
      first = false
      result.applied.push(campo)
    } else {
      result.unmatched[campoBackend] = msg
    }
  }
  return result
}

export interface HandleErrorOptions<T extends FieldValues> {
  form?: FormLike<T>
  fieldMap?: Record<string, string>
  /** Título del toast (ej. "No se pudo guardar el producto"). */
  title?: string
}

export function useApiErrorHandler() {
  const toast = useToast()

  return useCallback(
    <T extends FieldValues = FieldValues>(error: unknown, opts: HandleErrorOptions<T> = {}): void => {
      const { form, fieldMap, title } = opts

      if (!(error instanceof ApiError)) {
        console.error(error)
        toast.error(error instanceof Error ? error.message : 'Ocurrió un error inesperado.', title)
        return
      }

      if (error.isHandledGlobally) return // 401: redirección gestionada por el cliente

      if (error.isForbidden) {
        toast.error(error.detail, title ?? 'Acceso denegado')
        return
      }

      if (error.isValidation) {
        if (form) {
          const { applied, unmatched } = applyFieldErrors(form, error, fieldMap)
          const extra = Object.entries(unmatched).map(([k, v]) => `${k}: ${v}`)
          if (extra.length > 0) toast.error(extra.join(' · '), title ?? 'Datos no válidos')
          else if (applied.length === 0) toast.error(error.detail, title ?? 'Datos no válidos')
          return
        }
        const extra = Object.entries(error.fieldErrors).map(([k, v]) => `${k}: ${v}`)
        toast.error(extra.length ? extra.join(' · ') : error.detail, title ?? 'Datos no válidos')
        return
      }

      if (error.isConflict) {
        toast.error(error.detail, title ?? 'Operación no permitida')
        return
      }

      toast.error(error.detail, title)
    },
    [toast],
  )
}
