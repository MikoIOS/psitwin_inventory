# Integración del clon de Dylan

Origen: clon local `/home/m4ik_1/Documentos/dyl/PsiTwin_inventory`, commit
`98a383d`. Destino: `psitwin-publicacion`, partiendo de `4e8f4b9`.
Se compararon los cambios desde `f92f092`, cuya aplicación coincide con la
importación inicial del destino. Los historiales Git no comparten un ancestro;
la integración conserva el historial del destino y aplica los cambios de código.

## Cambios incorporados

- Abastecimiento con ofertas, reserva de cantidades, pedidos y recepciones.
- Niveles de racks, consultas de existencias y plano del almacén.
- Reportes de inventario PDF/Excel, análisis de demanda e historial.
- Mejoras de Saiki, voz local, consultas de sensores y autenticación.
- Pruebas del backend, Vitest y escenarios Playwright.

Se conservaron el proxy hacia `psitwin-backend.onrender.com`, los dominios
de `psitwin-inventory.vercel.app`, las plantillas de despliegue existentes y la
eliminación del aviso de verificación del proveedor. No se copiaron archivos
`.env`, bases de datos, credenciales, configuración de asistentes ni reportes
generados del otro clon.

## Ajustes de compatibilidad

- La creación de existencias conserva `id_nivel`; las filas usan el ID del detalle.
- La recepción envía cabecera de almacén, rack y nivel al backend; el operario
  no intenta definir umbrales reservados a la empresa.
- El índice único de ubicaciones ahora incluye el nivel. Se crea el reemplazo
  antes de retirar el índice anterior.
- Las alertas de inventario mantienen su índice parcial; las de sensor tienen
  una restricción por dispositivo, tipo y parámetro, sin colisión por IDs nulos.
- Los intérpretes opcionales de IA/voz y las configuraciones Playwright admiten
  Linux y Windows. Vitest usa procesos separados.

## Preparación del entorno

Instalar dependencias en un entorno virtual del proyecto:

```bash
cd backend
python -m pip install -r requirements-dev.txt
cd ../frontend
npm ci
npm run build
npm run test:ui
cd ../backend
python -m pytest tests -q
```

Las pruebas de integración crean bases de datos temporales; requieren una
instancia MongoDB de pruebas accesible. Las pruebas con Ollama o AutoGluon
reales son optativas y necesitan sus respectivos servicios y modelos.

Para Playwright en Linux, instalar Chromium con `npx playwright install chromium`
desde `frontend`. Se puede seleccionar Python con `PSITWIN_TEST_PYTHON` y el
navegador con `PSITWIN_TEST_BROWSER`.

## Antes de desplegar

1. Revisar la migración aditiva descrita en `ABASTECIMIENTO_IMPLEMENTACION.md`.
   Primero ejecutar el plan sin escritura:
   `python scripts/migrar_abastecimiento.py` desde `backend`.
   Aplicar solo con los escritores detenidos y un directorio nuevo de respaldo,
   usando `--apply --backup <directorio>`. Esta integración no la ejecutó.
2. El nuevo registro de empresas usa un enlace enviado por correo: necesita
   transporte SMTP operativo. Las cuentas antiguas conservan su acceso. El
   estado `EMAIL_ENABLED=false` no habilita la entrega de enlaces.
3. El motor nuevo de pronósticos usa AutoGluon en un entorno aislado. Sus pesos
   y los de voz no están incluidos en Git: configurar las rutas y ejecutar
   las verificaciones reales antes de presentar esas funciones como disponibles.
4. Conservar las variables propias de Render/Vercel. Los ejemplos no reemplazan
   las variables ya configuradas en los servicios.

No se publicaron despliegues ni se modificaron datos de producción durante la
integración. Los scripts locales de simulación y la carga demo previa quedaron
fuera del conjunto de cambios incorporados.

## Verificación de esta integración (29/10/2026)

- TypeScript y build de Vite: aprobados.
- Vitest: 106 pruebas aprobadas en 23 archivos.
- Backend: 376 pruebas aprobadas y 26 subpruebas aprobadas; 55 omitidas
  (52 por MongoDB inaccesible y 3 integraciones optativas).
- La suite excluyó `test_warehouse_map.py` y una prueba de exportación porque
  `pypdf` no está instalado en los entornos disponibles. La dependencia está
  declarada en `requirements-dev.txt`; no se descargó por falta de red.
- Como comprobación independiente, se generaron reportes con existencias y
  vacíos: PDF leído con `pdftotext` y Excel leído con `openpyxl`, con cinco hojas
  y cantidades numéricas. Esto no sustituye las pruebas con MongoDB real.
- Playwright reconoció 4 escenarios de autenticación y 17 de Saiki,
  abastecimiento y planos. No pudieron ejecutarse: el servidor Vite recibe
  `listen EPERM` al abrir el puerto local en este sandbox.
- Sin conflictos Git pendientes ni errores de sintaxis en los 158 archivos
  Python añadidos/modificados.

La ejecución del backend usó un runner temporal fuera del repositorio con un
temporizador para despertar asyncio: el sandbox bloquea la señal de socket
entre hilos. No se sustituyeron servicios ni respuestas de la aplicación con
ese runner. Las pruebas conservan sus propios dobles y dependencias declaradas.

Además de los conflictos, se corrigió una regresión detectada por cinco pruebas
de Saiki: el manejador del plano interceptaba preguntas simples de ubicación de
productos. Esas preguntas vuelven a usar el catálogo y stock autorizados; los
filtros explícitos por almacén/zona/rack/nivel conservan la consulta detallada.
