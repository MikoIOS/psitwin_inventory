# Convenciones del frontend PsiTwin

Léelo antes de tocar un módulo. Las decisiones de negocio están en `docs/ESPECIFICACION.md` y el contrato
de la API en el `/openapi.json` del backend (el PDF es solo referencia histórica).

## Comandos

```bash
npm run dev        # Vite en http://localhost:5173
npm run typecheck  # tsc --noEmit (TypeScript strict + exactOptionalPropertyTypes + noUncheckedIndexedAccess)
npm run build      # typecheck + build de producción
```

La app llama a `/api/v1` y en desarrollo Vite lo reenvía a `VITE_PROXY_TARGET` (default `http://localhost:8000`), evitando CORS. `VITE_API_URL` solo si se quiere llamar al backend directo (ver `.env.example`).

## Estructura

```
src/
  api/                 TODO el acceso HTTP y los tipos. Nada de fetch fuera de aquí.
    client.ts          fetch wrapper, ApiError; 401 → /login; 403 PASSWORD_CHANGE_REQUIRED → marca la sesión; otro 403 → error
    types.ts           entidades, bodies Create/Update y enums (union types)
    enums.ts           etiquetas en español, opciones de <Select>, ACCIONES_ORDEN, MOTIVOS_MANUALES_POR_TIPO
    queryKeys.ts       query keys centralizadas
    normalize.ts       id → id_xxx, lat/lon string → number, recepción.detalles
    <recurso>.ts       `xxxApi` (funciones por endpoint) + hooks TanStack Query
    ubicaciones.ts     useUbicaciones(): mapa rack → zona → almacén de la empresa
  auth/                SessionContext (token + rol + datos), useRol(), useEmpresa()/useIdEmpresa(), guards (RequireAuth, RequireRol)
  components/
    ui/                kit de UI (importar desde '@/components/ui')
    selects/           selects conectados a datos (importar desde '@/components/selects')
    layout/            AppLayout (sidebar/drawer), navegación, RouteError, ModulePlaceholder
  features/<modulo>/   páginas y componentes de cada módulo (una carpeta por módulo)
  lib/                 utilidades puras: format, zod helpers, stock, ordenes, cn, storage
  paths.ts             constructores de rutas (paths.orden(id), ...)
  routes.tsx           registro de rutas (lazy por página)
```

Alias: `@/` → `src/`.

## Añadir o implementar un módulo

1. Trabaja dentro de `src/features/<modulo>/`. Las páginas ya existen como placeholder con un comentario
   `TODO(módulo …)` que describe el alcance: reemplaza el contenido, mantén el `export default`.
2. Componentes propios del módulo (formularios, modales) van en la misma carpeta (`ZonaForm.tsx`, …).
   Si algo es reutilizable por varios módulos, muévelo a `components/`.
3. Ruta nueva: añade el constructor en `src/paths.ts` y regístrala en `src/routes.tsx` con
   `page(() => import('@/features/...'))`. Enlaces siempre con `paths.xxx`, nunca strings sueltos.
4. Ítem de menú nuevo: `src/components/layout/navigation.ts`.
5. No edites `src/api/*` para lógica de pantalla. Si falta un endpoint o un campo, añádelo en el archivo del
   recurso (función en `xxxApi` + hook) respetando las mismas convenciones.

Estructura típica de una página:

```tsx
export default function ProveedoresPage() {
  const q = useProveedores()
  return (
    <>
      <PageHeader title="Proveedores" eyebrow="Reposición" actions={<Button icon="plus">Nuevo proveedor</Button>} />
      <DataTable caption="Proveedores" data={q.data} loading={q.isLoading} error={q.error} onRetry={q.refetch}
        rowKey={(p) => p.id_proveedor} columns={[...]} empty={<EmptyState title="Sin proveedores" />} />
    </>
  )
}
```

## Roles y permisos

Contrato: `docs/ROLES.md` (con «Desviaciones») + OpenAPI. Resumen por pantalla en `docs/ESPECIFICACION.md`.

- **No se duplican pantallas por rol.** Una página, y dentro: `const { esEmpresa, esOperario, esProveedor, idAlmacen } = useRol()`
  para mostrar u ocultar acciones (el backend responde 403 de todos modos). Nada de botones deshabilitados "por permiso": se ocultan.
- **Rutas**: `routes.tsx` agrupa con `<RequireRol roles={[...]} />`; una ruta ajena vuelve a `/`. **Menú**: `roles` de cada
  ítem en `navigation.ts`. Ambos deben coincidir. `/` lo resuelve `features/inicio/InicioPorRol`.
- **Sesión**: `useSession()` → `rol`, `empresa`, `operario`, `proveedor`, `debeCambiarPassword`. `RequireAuth` la refresca con
  `/auth/me` y manda a `/cambiar-password` mientras haya contraseña temporal.
- **Datos por rol**: `useIdEmpresa()` devuelve `undefined` para PROVEEDOR, así los listados `/x/empresa/{id}` quedan
  deshabilitados; los hooks globales (`useZonas`, `useRacks`, `useInventarios`, `useMovimientos`, `useRecepciones`) también.
  `useOperarios()` solo corre para EMPRESA. `useOrdenes()` usa `/proveedor/me` para el PROVEEDOR. `useNombres()` completa
  con la sesión lo que el rol no puede listar.
- **Cuentas** (`@/components/CredencialesModal`): `PasswordTemporalInput` (generar / copiar), `RestablecerPasswordModal`
  (también «Dar acceso»), `CredencialesEntregaModal`, `BadgesCuenta`. Sirven para operarios y proveedores.
- **Solicitudes**: `ACCIONES_ORDEN.puedeValidar / puedeDevolver / puedeCancelar` (EMPRESA), `puedeEditar / puedeReenviar /
  puedeEliminar / puedeRecibir` (OPERARIO; `puedeRecibir` también habilita el despacho del PROVEEDOR). Hooks:
  `useValidarOrden`, `useDevolverOrden`, `useReenviarOrden`, `useDespacharOrden`.
- **Racks**: la carga viene del backend (`rack.carga_kg`, `rack.libre_kg`); `@/lib/racks` solo tiene presentación.
  Para elegir destino: `useRacksDisponibles(idAlmacen, idProducto, cantidad)`.

## Hooks de API

- Consultas: `useXxx(id)`, `useXxxPorYyy(id)` (se deshabilitan solas si el id es `undefined`).
- Recursos de la empresa (almacenes, operarios, proveedores, órdenes, productos) ya filtran por la empresa
  de la sesión: `useAlmacenes()`, `useOperarios({ soloActivos, idAlmacen, estrictoAlmacen })`,
  `useProveedores({ soloActivos })`, `useOrdenes()`, `useProductos()`. Con `idAlmacen`, los operarios antiguos SIN almacén
  no se excluyen salvo `estrictoAlmacen` (recepción: el backend exige el almacén de la orden). El almacén del operario se
  fija al crearlo (no editable). Turno/estado de operario son texto libre: `etiquetaTurno()`, `operarioActivo()`.
- El backend toma la empresa (y el operario / proveedor autor) del TOKEN: los bodies no llevan `id_empresa` ni `id_operario`.
- Mutaciones de update: `mutate({ id, body })`. Delete: `mutate(id)`.
- Las invalidaciones ya están hechas en cada hook (p. ej. `useCreateMovimiento` invalida inventarios y
  movimientos; `useCreateRecepcion` / `useResolverDetalleRecepcion` invalidan órdenes, detalles de reposición,
  recepciones, inventarios y movimientos). No invalides a mano salvo casos especiales, y siempre con `queryKeys`.
- `id_empresa`: `useEmpresa().id_empresa` o `useIdEmpresa()`. Dentro del layout protegido siempre está cargado.
- Inventarios, recepciones y movimientos no tienen filtro por empresa en el backend: usa
  `useUbicaciones().perteneceAEmpresa(inv.id_rack)` para acotar y `porRack.get(id).etiqueta` para mostrar la ubicación
  ("Almacén › Zona › Rack A-01", con el `codigo` real del rack). Los movimientos traen `id_producto` e `id_rack`.
- Estado de stock: `estadoStock(inv)` / `resumenStock(invs)` en `@/lib/stock` (fuente = `Inventario.stock_actual`).
- Pendientes de una orden: `calcularPendientes(useDetallesReposicion(id).data, useDetallesRecepcionPorOrden(id).data)`.
- Acciones de orden: `ACCIONES_ORDEN.puedeAprobar(estado)`, etc. (`@/api/enums`).
- Motivos del formulario manual de movimientos: `motivosManualesOpciones(tipo)` (nunca RECEPCION).
- Recepción (UN paso): `useCreateRecepcion()` con `detalles` (≥ 1 línea, cada una con `id_inventario`) crea la recepción e
  ingresa al inventario. NUNCA llamar después a `POST /recepciones/{id}/detalles` (duplicaría el ingreso). Líneas
  EN_EVALUACION: `useResolverDetalleRecepcion()` (ver ESPECIFICACION). `RecepcionCrearModal` (solo OPERARIO) precarga el
  despacho, elige por línea un rack de `/racks/disponibles` y crea el inventario si falta; `DetallesRecepcionTable` muestra las líneas y «Resolver».
- Ocupación de racks (unidades), calculada en el cliente: `ocupacionRack(rack, inventariosDelRack)` de `@/lib/racks`;
  grilla reutilizable `RackGrilla` (`features/almacenes`). El backend no valida capacidad.

## Formularios

react-hook-form + zod. Los inputs dan strings; usa los helpers de `@/lib/zod` que convierten al tipo del body:

```tsx
const schema = z.object({ nombre: texto(), capacidad: numero({ min: 0, entero: true }), temperatura_min: numeroOpcional() })
type In = z.input<typeof schema>; type Out = z.output<typeof schema>
const form = useForm<In, unknown, Out>({ resolver: zodResolver(schema), defaultValues: { nombre: '', capacidad: '', temperatura_min: '' } })
```

- `numStr(v)` para pasar números a `defaultValues` al editar.
- `textoOpcional()` → `null` si vacío; `idRequerido()` para selects.
- Referencia completa: `src/features/almacenes/AlmacenForm.tsx` (crear/editar, reutilizable).

## Componentes UI (`@/components/ui`)

| Componente | Props principales |
|---|---|
| `Button` | `variant` primary/secondary/ghost/subtle/danger, `size` sm/md/lg, `loading`, `icon`, `iconRight`, `iconOnly` (+`aria-label`), `fullWidth` |
| `LinkButton` | igual que Button pero es un `<Link to>` (no anidar Button dentro de Link) |
| `Field` | `label`, `error`, `hint`, `required`, `hideLabel` — envuelve un control y conecta id/aria |
| `Input` | nativo + `size` md/lg, `suffix` ("m²", "°C") |
| `Select` | nativo + `options`, `placeholder` (o `false`), `size` |
| `Textarea`, `Checkbox` (`label`, `description`) | nativos, compatibles con `register()` |
| `Card` | `title`, `description`, `eyebrow`, `actions`, `padding` none/sm/md, `accent` |
| `Badge` | `tone` neutral/info/success/warning/danger/accent |
| `StatusBadge` | `estado`: estados de orden, ACTIVO/INACTIVO, estados de rack, tipos y motivos de movimiento |
| `StockBadge` | `inventario` o `estado` (SIN_STOCK/STOCK_BAJO/STOCK_OK/SOBRE_STOCK) |
| `Modal` | `open`, `onClose`, `title`, `description`, `footer`, `size` sm/md/lg/xl, `dismissable` |
| `ConfirmDialog` | `open`, `title`, `description`, `confirmLabel`, `tone` danger/primary, `loading`, `onConfirm`, `onCancel` |
| `DataTable` | `columns` (`{ id, header, cell, align, mobile: 'title'|'badge'|'field'|'hidden' }`), `data`, `rowKey`, `caption`, `loading`, `error`, `onRetry`, `empty`, `onRowClick`, `actions` |
| `EmptyState` / `ErrorState` | `icon`, `title`, `description`, `action` / `error`, `onRetry` |
| `Spinner` / `LoadingBlock` | `size`, `label` |
| `PageHeader` | `title`, `eyebrow`, `description`, `actions`, `back: { to, label }`, `meta` |
| `useToast()` | `.success(msg, título?)`, `.error()`, `.info()`, `.warning()` |
| `Icon` | `name` (ver `Icon.tsx`), `className` |

Formularios en modal: usa `formId` en el `<form>` y `<Button type="submit" form={formId}>` en el `footer`.

Selects de datos (`@/components/selects`): `AlmacenSelect`, `ZonaSelect idAlmacen`, `RackSelect idZona soloDisponibles?`,
`ProductoSelect excluir? filtrar?`, `OperarioSelect soloActivos=true idAlmacen?`, `ProveedorSelect soloActivos=true`,
`InventarioSelect idProducto idAlmacen? emptyText?`. Todos aceptan `{...register('campo')}`. En cascada, al cambiar
el padre resetea el hijo con `setValue('id_zona', '')`.

## Manejo de errores

`ApiError { status, detail, fieldErrors }` (de `@/api/client`). `detail` ya viene en español listo para mostrar.

```tsx
const handleError = useApiErrorHandler()
crear.mutate(body, {
  onSuccess: () => { toast.success('Proveedor creado'); cerrar() },
  onError: (e) => handleError(e, { form, title: 'No se pudo crear el proveedor' }),
})
```

- **422** → errores en los campos del form (`applyFieldErrors`); los que no mapean a un campo van a un toast.
  Si el nombre del campo del form difiere del backend: `handleError(e, { form, fieldMap: { id_rack: 'rack' } })`.
- **409** → toast con el `detail` del backend (stock insuficiente, orden en estado inválido, operario inactivo…).
- **404** → toast. **Red / 5xx** → mensaje genérico (5xx ya se registra con `console.error`).
- **401** y **403 `PASSWORD_CHANGE_REQUIRED`** → los gestiona el cliente (logout / `/cambiar-password`); no hagas nada (`e.isHandledGlobally`).
- **403** → NO cierra la sesión: `useApiErrorHandler` muestra un toast «Acceso denegado»; en queries, `ErrorState`.
- Queries: muestra `<ErrorState error={q.error} onRetry={q.refetch} />` (DataTable ya lo hace).

## Estilo

- Todo el texto de la interfaz en español.
- Colores solo por tokens (`bg-surface`, `text-fg-muted`, `border-border`, `bg-accent`, `text-danger`, …) definidos
  en `src/index.css`; tema claro/oscuro automático. No uses colores de la paleta Tailwind (`bg-gray-100`, …).
- Monoespaciada (`font-mono`) para códigos, RUC e ids; `tabular` para columnas numéricas; `label-stencil` para rótulos.
- Responsive: diseña primero para móvil (la recepción debe usarse en tablet/celular). Botones de acción
  principales `size="lg"` en móvil si el formulario es de uso en planta.
- Accesibilidad: todo control con `Field`/label; botones solo-icono con `aria-label`; no quitar el foco visible.
