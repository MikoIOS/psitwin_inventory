/**
 * Helpers de zod para formularios con react-hook-form.
 *
 * Los <input> devuelven strings; estos esquemas aceptan string y producen el tipo del body.
 * Declarar el form así (input ≠ output):
 *
 *   const schema = z.object({ nombre: texto(), capacidad: numero({ min: 0, entero: true }) })
 *   type Entrada = z.input<typeof schema>; type Salida = z.output<typeof schema>
 *   const form = useForm<Entrada, unknown, Salida>({ resolver: zodResolver(schema), defaultValues: {...strings} })
 */
import { z } from 'zod'

export const MSG = {
  requerido: 'Campo obligatorio',
  numero: 'Debe ser un número válido',
  entero: 'Debe ser un número entero',
  correo: 'Correo electrónico no válido',
  seleccion: 'Selecciona una opción',
} as const

/** Texto obligatorio (recortado). */
export function texto(opts: { max?: number; min?: number; mensaje?: string } = {}) {
  let s = z.string().trim().min(opts.min ?? 1, opts.mensaje ?? MSG.requerido)
  if (opts.max) s = s.max(opts.max, `Máximo ${opts.max} caracteres`)
  return s
}

/** Texto opcional: "" → null. */
export function textoOpcional(opts: { max?: number } = {}) {
  let s = z.string().trim()
  if (opts.max) s = s.max(opts.max, `Máximo ${opts.max} caracteres`)
  return s.transform((v) => (v === '' ? null : v))
}

/** Id de un <select> (obligatorio). */
export function idRequerido(mensaje: string = MSG.seleccion) {
  return z.string().min(1, mensaje)
}

export function correo() {
  return z.string().trim().min(1, MSG.requerido).pipe(z.email(MSG.correo))
}

/** Correo opcional: "" → null; si se informa, debe ser válido. */
export function correoOpcional() {
  return z
    .string()
    .trim()
    .transform((v) => (v === '' ? null : v))
    .pipe(z.email(MSG.correo).nullable())
}

export interface NumeroOpts {
  min?: number
  max?: number
  /** Estrictamente mayor que. */
  mayorQue?: number
  entero?: boolean
  /** Máximo de decimales permitidos (ej. 6 para coordenadas). */
  maxDecimales?: number
}

function numeroBase(o: NumeroOpts) {
  let n = z.number({ error: MSG.numero })
  if (o.entero) n = n.int(MSG.entero)
  if (o.min !== undefined) n = n.min(o.min, `Debe ser mayor o igual a ${o.min}`)
  if (o.mayorQue !== undefined) n = n.gt(o.mayorQue, `Debe ser mayor que ${o.mayorQue}`)
  if (o.max !== undefined) n = n.max(o.max, `Debe ser menor o igual a ${o.max}`)
  return n
}

const aNumero = (v: string) => Number(v.replace(',', '.'))

function decimalesOk(v: string, max: number | undefined): boolean {
  if (max === undefined) return true
  const dec = v.replace(',', '.').split('.')[1]
  return !dec || dec.length <= max
}

/** Número obligatorio desde un input de texto/number. */
export function numero(o: NumeroOpts = {}) {
  return z
    .string()
    .trim()
    .min(1, MSG.requerido)
    .refine((v) => decimalesOk(v, o.maxDecimales), `Máximo ${o.maxDecimales ?? 0} decimales`)
    .transform(aNumero)
    .pipe(numeroBase(o))
}

/** Número opcional: "" → null. */
export function numeroOpcional(o: NumeroOpts = {}) {
  return z
    .string()
    .trim()
    .transform((v) => (v === '' ? null : aNumero(v)))
    .pipe(numeroBase(o).nullable())
}

/** Convierte un número (o null) a string para `defaultValues`. */
export function numStr(v: number | null | undefined): string {
  return v === null || v === undefined ? '' : String(v)
}
