import { test, expect, type Page } from '@playwright/test'

// Browser integration with deterministic HTTP mocks; backend business rules are
// separately tested against an isolated real MongoDB database.
async function setup(page: Page, role: 'EMPRESA' | 'OPERARIO' | 'PROVEEDOR', fail = false) {
  const empresa = { id_empresa: 'test', nombre: 'Empresa de prueba' }
  const actor = { id_empresa: 'test', id_operario: 'o', id_proveedor: 'v', id_almacen: 'w', nombre: 'Usuario' }
  const session = { rol: role, empresa, operario: role === 'OPERARIO' ? actor : undefined, proveedor: role === 'PROVEEDOR' ? actor : undefined }
  const writes: any[] = []
  await page.addInitScript(session => { localStorage.setItem('psitwin.token', 'browser-isolated'); localStorage.setItem('psitwin.sesion', JSON.stringify(session)) }, session)
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    if (route.request().method() !== 'GET') {
      writes.push({ path, body: route.request().postDataJSON() })
      return route.fulfill({ json: { id_oferta: 'offer', ...writes.at(-1).body } })
    }
    if (fail && path === '/abastecimiento/seguimiento') return route.fulfill({ status: 503, json: { detail: 'Controlled failure' } })
    const data = path === '/auth/me' ? session : path === '/empresas/me' ? empresa
      : path.includes('/almacenes') ? [{ id_almacen: 'w', id_empresa: 'test', nombre: 'Almacén de prueba' }]
      : path === '/abastecimiento/catalogo' ? [{ id_producto: 'p', nombre: 'Mango Kent', unidad: 'kg', familia: 'Frutas', categoria: 'Tropicales' }]
      : path === '/abastecimiento/ofertas' ? [{ id_oferta: 'offer', id_producto: 'p', producto: 'Mango Kent', id_proveedor: 'v', proveedor: 'Proveedor', unidad: 'kg', familia: 'Frutas', categoria: 'Tropicales', precio_centimos: 450, cantidad_total: 100, cantidad_disponible: 80, cantidad_reservada: 0, cantidad_despachada: 20, activa: true }]
      : path === '/abastecimiento/seguimiento' ? [{ id_orden: 'order', id_producto: 'p', id_proveedor: 'v', proveedor: 'Proveedor', telefono: '987654321', estado: 'PARCIAL', fecha: '2026-01-01T12:00:00Z', unidad: 'kg', solicitada: 20, despachada: 20, recibida: 20, aceptada: 15, rechazada: 5, faltante: 5, diferencia_despacho: 0, motivos: ['Mango deteriorado'] }]
      : path === '/abastecimiento/historial-pedidos' ? { registros: [], totales_por_unidad: {} } : []
    return route.fulfill({ json: data })
  })
  await page.goto('/abastecimiento')
  await expect(page.getByRole('heading', { name: 'Abastecimiento', exact: true })).toBeVisible()
  return writes
}

test('company sees accepted stock, rejection reason and records an explicit shortfall decision', async ({ page }) => {
  const writes = await setup(page, 'EMPRESA')
  await expect(page.getByText('Motivo registrado: Mango deteriorado')).toBeVisible()
  await expect(page.getByText(/Aceptado: 15.*Faltante por aceptar: 5 kg/)).toBeVisible()
  await expect(page.locator('a[href="tel:987654321"]')).toBeVisible()
  await page.getByRole('button', { name: 'Mantener pendiente', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Confirmar decisión' })).toBeDisabled()
  await page.getByRole('textbox', { name: 'Motivo', exact: true }).fill('Esperar entrega del proveedor')
  await page.getByRole('button', { name: 'Confirmar decisión' }).click()
  await expect.poll(() => writes.length).toBe(1)
  expect(writes[0]).toEqual({ path: '/abastecimiento/solicitudes/order/pendiente', body: { decision: 'MANTENER', motivo: 'Esperar entrega del proveedor' } })
  await expect(page.getByRole('button', { name: 'Nueva solicitud' })).toHaveCount(0)
})

test('operator reviews available quantities and cannot resolve company shortfalls', async ({ page }) => {
  await setup(page, 'OPERARIO')
  await expect(page.getByRole('button', { name: 'Mantener pendiente', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Nueva solicitud' }).click()
  await page.getByRole('combobox', { name: 'Proveedor', exact: true }).selectOption('v')
  await page.getByRole('spinbutton', { name: 'Cantidad de Mango Kent (kg)' }).fill('20.5')
  await page.getByRole('button', { name: 'Revisar solicitud' }).click()
  await expect(page.getByRole('button', { name: 'Confirmar solicitud' })).toBeVisible()
  await expect(page.getByRole('status')).toContainText('Confirma para enviar a aprobación')
})

test('supplier edits external offer independently of warehouse stock', async ({ page }) => {
  const writes = await setup(page, 'PROVEEDOR')
  await page.getByRole('button', { name: 'Configurar ofertas' }).click()
  await page.getByRole('combobox', { name: 'Producto del catálogo' }).selectOption('p')
  await page.getByRole('spinbutton', { name: 'Precio por kg (PEN)' }).fill('4.75')
  await page.getByRole('button', { name: 'Guardar oferta', exact: true }).click()
  await expect.poll(() => writes.length).toBe(1)
  expect(writes[0].path).toBe('/abastecimiento/ofertas')
  expect(writes[0].body).toMatchObject({ id_producto: 'p', unidad: 'kg', precio: '4.75', cantidad_total: 100 })
  await expect(page.getByRole('button', { name: 'Historial de pedidos', exact: true })).toHaveCount(0)
})

test('technical tracking error is distinct from no requests', async ({ page }) => {
  await setup(page, 'EMPRESA', true)
  await expect(page.getByRole('alert').filter({ hasText: 'No se pudo consultar el seguimiento' })).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('No hay solicitudes registradas para tu sesión.')).toHaveCount(0)
})


test('a catalog product opens its supplier offer editor directly', async ({ page }) => {
  await setup(page, 'PROVEEDOR')
  await page.goto('/abastecimiento?producto=p')
  await expect(page.getByRole('combobox', { name: 'Producto del catálogo' })).toHaveValue('p')
  await expect(page.getByRole('spinbutton', { name: 'Precio por kg (PEN)' })).toBeVisible()
})
