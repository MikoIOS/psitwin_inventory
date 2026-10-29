import { test, expect, type Page } from '@playwright/test'

async function setup(page: Page, fail = false) {
  const company = { id_empresa: 'test', nombre: 'Empresa de prueba' }
  const session = { rol: 'EMPRESA', empresa: company }
  const writes: string[] = []
  let quantity = 12
  let location = 2
  let expanded = false
  let critical = false
  let removed = false
  await page.addInitScript(session => {
    localStorage.setItem('psitwin.token', 'isolated-browser')
    localStorage.setItem('psitwin.sesion', JSON.stringify(session))
  }, session)
  const draft = { id_reporte: 'report', estado: 'CONFIRMAR', formato: 'pdf', destinatario: 'empresa@example.test', alcance: 'Almacén de prueba', resumen: { productos_distintos: 1 } }
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    if (path.endsWith('/plano')) {
      if (fail) return route.fulfill({status:503,json:{detail:'Consulta no disponible'}})
      return route.fulfill({json:{almacen:{id:'w',nombre:'Almacén de prueba'},zonas:[{id:'z',nombre:'Zona B',max_racks:4},...(expanded ? [{id:'zd',nombre:'Zona D',max_racks:3}] : [])],racks:[{id_rack:'r',id_zona:'z',codigo:'R1',tipo_rack:'Convencional',max_niveles:expanded ? 6 : 5,estado:'DISPONIBLE'},...(expanded ? [{id_rack:'r2',id_zona:'zd',codigo:'R02',tipo_rack:'Selectivo',max_niveles:1,estado:'DISPONIBLE'}] : [])],niveles:[1,2,3,4,5,...(expanded ? [6] : [])].filter(n => !removed || n !== 5).map(numero => ({id_nivel:`n${numero}`,id_rack:'r',numero,codigo:`N-${numero}`,monitoreo:critical && numero === 3 ? 'critico' : 'sin_datos'})),inventario:[{id_detalle_inventario:'di',id_producto:'p',producto:'Mango Kent',stock_actual:quantity,ubicacion_valida:true,unidad:'kg',estado:'NORMAL',id_zona:'z',id_rack:'r',id_nivel:`n${location}`,nivel:location}],alertas:[],generado_en:'2026-10-29T12:00:00Z'}})
    }
    if (path === '/inventario-reportes/exportar') return route.fulfill({body:'%PDF-1.4 controlled browser test',contentType:'application/pdf',headers:{'Content-Disposition':'attachment; filename="inventario.pdf"'}})
    if (route.request().method() !== 'GET') {
      writes.push(path)
      if (path.endsWith('/confirmar')) return route.fulfill({json:{...draft,estado:'ACEPTADO_SMTP'}})
      return route.fulfill({json:draft})
    }
    return route.fulfill({json:path === '/auth/me' ? session : path === '/empresas/me' ? company : path.startsWith('/almacenes') ? [{id_almacen:'w',id_empresa:'test',nombre:'Almacén de prueba'}] : []})
  })
  return { writes, changeQuantity: (n:number) => {quantity=n}, remoteChange: () => { location=3; expanded=true; critical=true; removed=true }, resolveAlert: () => {critical=false} }
}

test('remote structure, stock and level alert changes appear without manual refresh', async ({page}) => {
  const server = await setup(page)
  await page.goto('/almacenes/w/plano')
  await expect(page.locator('[data-nivel="n2"]')).toContainText('Mango Kent')
  server.remoteChange()
  await expect(page.getByText('Zona D',{exact:true})).toBeVisible({timeout:12000})
  await expect(page.getByText('Rack R02 — Selectivo',{exact:true})).toBeVisible()
  await expect(page.locator('[data-nivel="n2"]')).toContainText('Vacío')
  await expect(page.locator('[data-nivel="n3"]')).toContainText('Mango Kent')
  await expect(page.locator('[data-nivel="n3"]')).toHaveAttribute('data-estado','critico')
  await expect(page.locator('[data-nivel="n2"]')).toHaveAttribute('data-estado','sin_datos')
  await expect(page.locator('[data-nivel="n5"]')).toHaveCount(0)
  await expect(page.locator('[data-nivel="n6"]')).toBeVisible()
  server.resolveAlert()
  await expect(page.locator('[data-nivel="n3"]')).toHaveAttribute('data-estado','sin_datos',{timeout:12000})
})

test('interactive map has five vertical levels and refreshes actual location quantities', async ({page}) => {
  const context = await setup(page)
  await page.goto('/almacenes/w/plano')

  await expect(page.getByRole('button',{name:/Nivel \d/})).toHaveCount(5)
  await page.getByRole('button',{name:/Nivel 2/}).click()
  await expect(page.getByRole('cell',{name:'12',exact:true})).toBeVisible()
  context.changeQuantity(9)
  await page.getByRole('button',{name:'Actualizar plano'}).click()
  await expect(page.getByRole('cell',{name:'9',exact:true})).toBeVisible()
  await page.getByRole('link',{name:'Preguntar a Saiki sobre esta ubicación'}).click()
  await expect(page).toHaveURL(/\/saiki/)
})

test('inventory downloads PDF and sends only after explicit confirmation', async ({page}) => {
  const {writes} = await setup(page)
  await page.goto('/inventario')
  await page.getByRole('button',{name:'Exportar inventario',exact:true}).click()
  const download = page.waitForEvent('download')
  await page.getByRole('button',{name:'Descargar PDF',exact:true}).click()
  expect((await download).suggestedFilename()).toBe('inventario.pdf')
  await page.getByRole('button',{name:'Enviar PDF al correo',exact:true}).click()
  await expect(page.getByText('empresa@example.test',{exact:true})).toBeVisible()
  expect(writes).toEqual(['/inventario-reportes/solicitudes'])
  await page.getByRole('button',{name:'Confirmar envío',exact:true}).click()
  await expect(page.getByRole('status')).toContainText('no confirma recepción')
  expect(writes).toEqual(['/inventario-reportes/solicitudes','/inventario-reportes/envios/report/confirmar'])
  await expect(page.getByRole('button',{name:'Confirmar envío',exact:true})).toHaveCount(0)
})

test('map technical failure is distinct from an empty warehouse', async ({page}) => {
  await setup(page,true)
  await page.goto('/almacenes/w/plano')
  await expect(page.getByRole('alert')).toContainText('No se pudo consultar el plano')
  await expect(page.getByText('No hay zonas registradas en este almacén.')).toHaveCount(0)
})
