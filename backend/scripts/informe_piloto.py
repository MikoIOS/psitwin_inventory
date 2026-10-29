"""Assemble a reviewable report from captured evidence; never fabricates replies."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/piloto.local'
def load(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def cell(value):
    if not isinstance(value,str):value=json.dumps(value,ensure_ascii=False)
    return value.replace('|','/').replace('\r','').replace('\n','<br>')
checks,questions,manifest=load('pruebas.json'),load('saiki.json'),load('manifest.json')
regression=load('saiki_regresion.json')
counts=Counter(r['estado'] for r in checks)
correct={1,11,16,19,20,21,22,23,24,25,26,28,34,42,46}
partial={12,18,29,30,31,40,41,45}
truth={
1:'MongoDB: 10 productos',2:'Azúcar=1, Aceite=0; mínimo=5 por ubicación',3:'Arroz=41 al cierre; 42 antes de salida por vencimiento',4:'Leche en C-01',5:'Aceite=0',6:'Arroz=41',7:'Faltantes observables, sin pronóstico de compra válido',8:'Gaseosa=70, Arroz=41, Agua=25',9:'Venta de arroz=8; vencimiento=1 separado',10:'Ventas de arroz=8, azúcar=3, galletas=2',11:'Una entrada de 20',12:'Última venta: azúcar, 3 unidades',13:'No hay AJUSTE; API lo rechaza',14:'Entrada=20',15:'No hay movimientos de ayer; los 6 son del día de ejecución',16:'4 racks',17:'A-01: Gaseosa=70; no otros productos',18:'Bebidas: A-01 y A-02',19:'Arroz en B-01',20:'Solo C-01 tiene sensor',21:'Último valor=4 °C, lectura desactualizada al preguntar',22:'A-01 sin sensores',23:'Sin incidentes activos al cierre; no prueba seguridad actual',24:'Sin lecturas de ayer',25:'Un dispositivo con lectura antigua; no hardware físico',26:'Humedad 6 valores: mínimo20, máximo80, promedio55 %',27:'No hay sensor PIR; no confundir con 6 movimientos de stock',28:'Tres incidentes históricos resueltos; ninguno activo',29:'Producto nuevo sin historia suficiente; no forecast válido',30:'Sin compra predictiva calculable con estos datos',31:'Leche sin historial',32:'No inferible sin pronóstico válido',33:'No hay recomendación cuantitativa válida',34:'No hay historial importado',35:'Proveedor → Productos → Nuevo producto',36:'Empresa → almacén → zona → Nuevo rack',37:'Empresa → Monitoreo → Nuevo dispositivo',38:'Operario → Movimientos → SALIDA/VENTA',39:'Página Movimientos con filtros',40:'Alertas visibles en inventario/monitoreo según módulo',41:'Análisis, historial, horizonte y límites; sin garantía de precisión',42:'1 operario activo',43:'Almacén inexistente debe rechazarse o aclararse',44:'No seleccionar otro sensor para responder por uno sin lecturas',45:'Solicitar fechas concretas si el periodo no está definido',46:'Identidad y capacidades sin inventar datos'}
lines=['''# Informe de pruebas integrales de PsiTwin Inventory

Evaluación del 27 de octubre de 2026, hora de Lima. Todos los productos, cuentas,
movimientos y lecturas del piloto fueron **SIMULADOS**. Se ejecutaron FastAPI,
MongoDB y navegador reales; no se usaron ventas reales de una tienda.

## A. Resumen ejecutivo

**No listo para un piloto operativo ni una demostración completa de inventario en
la interfaz. Sí para levantamiento de datos y demo parcial supervisada de catálogo,
monitoreo y operaciones por API en una copia.**
Registro por enlace, login por contraseña, estructura física, catálogo según roles,
inventario por rack, recepción y ventas funcionan por API en los recorridos ejecutados.
La concurrencia ensayada no produjo stock negativo. El historial persiste en MongoDB.

Hay un fallo crítico de integración: Inventario en la interfaz muestra cero registros
aunque MongoDB tiene diez detalles. El cliente usa `/inventarios` como si devolviera
stock por rack, pero el backend devuelve cabeceras por almacén; los detalles están
en `/detalles-inventario` o `/inventarios/{id}/detalles`. Los formularios heredados
también requieren una revisión del contrato, no una corrección cosmética del contador.

Hay fallos altos pendientes: reenvíos de ventas duplican el descuento; Saiki responde
incorrectamente a varias preguntas o agota el tiempo; el riesgo llama a un adaptador
de historial inexistente; la serie operativa de demanda suma toda SALIDA, incluyendo
vencimientos. No debe presentarse esa serie como ventas minoristas puras.

AutoGluon cargó el artefacto local y produjo 90 días sobre 1.096 observaciones de
referencia. Eso verifica una inferencia técnica, **no precisión para los productos
nuevos ni validación comercial en la tienda**. El catálogo piloto no tiene historia
suficiente y la API lo comunica sin fabricar pronósticos.

## Entorno y protección de datos

Se comprobó HTTP 200 del frontend habitual y `/health` del backend. Ollama `/api/tags`
respondió 200 con `qwen3:4b`, cuantización Q4_K_M; disponer del modelo no equivale a
inferencia satisfactoria. Una consulta directa posterior al modelo agotó 15 s.

El runner creó una base con prefijo `psitwin_test_piloto_` y sufijo UUID; el estado
inicial estaba vacío. Los intentos anteriores se limpiaron comprobando prefijo y
que no coincidieran con la base configurada. No se ejecutó el lifespan de producción
en los recorridos ASGI. SMTP se capturó y MQTT se inyectó por el método real de
autenticación/ingesta, sin publicar a un broker ni conectar dispositivos físicos.
No se enviaron correos ni pedidos a terceros durante este piloto.

El snapshot excluye hashes de contraseña y tokens de dispositivos. Las únicas
credenciales del manifiesto son ficticias, de la empresa aislada. No se borraron ni
modificaron empresas reales. La segunda empresa para probar aislamiento también
era SIMULADA dentro de la misma base de prueba.

## Escenarios y resultados numéricos

Se crearon un almacén, tres zonas (bebidas, alimentos, refrigerados), cuatro racks,
un proveedor, un operario y diez productos. Precios, SKU y unidad comercial enviados
como extras no se guardan en el DTO de producto actual; no se presentan como campos
implementados. Hay lote, costo unitario y vencimiento en recepciones.

| Comprobación | Esperado | Observado |
|---|---:|---:|
| Arroz: recepción sobre 30 | 30+20=50 | 50 |
| Arroz: venta de 8 | 50−8=42 | 42 |
| Arroz: salida posterior por vencimiento | 42−1=41 | 41 |
| Azúcar: dos ventas simultáneas de 3 con saldo 4 | una aceptada, otra rechazada, saldo1 | 201 y409; saldo1 |
| Galletas: repetir una solicitud de venta de 1 | no duplicar un mismo evento | 18→17→16; fallo de idempotencia |
| Recepción repetida | no duplicar entrada | 409; una recepción persistida |
| Total unidades heterogéneas, solo control técnico | 190+20−13 ventas−1 vencimiento=196 | 196 |

Ese total mezcla productos distintos y no es un indicador comercial de demanda.
Las existencias finales por producto están en el manifiesto y snapshot.

## B. Tabla de pruebas ejecutadas

Cada ID se localiza en `artifacts/piloto.local/pruebas.json`; la columna obtenido
resume la respuesta real, y el JSON conserva los detalles. “Aprobado” de una
solicitud negativa significa que fue rechazada como se esperaba, no que esa
funcionalidad esté implementada. No probado para transferencias indica ausencia
de flujo público; no se fingió una transferencia con dos ventas.

''']
lines.append(f"Resumen de {len(checks)} comprobaciones: {dict(counts)}. Las 46 preguntas se valoran aparte, por contenido, no solo HTTP.\n")
lines.append('| ID | Módulo/acción | Datos | Esperado | Obtenido | Estado | Evidencia / error |\n|---|---|---|---|---|---|---|')
for r in checks:
    actual=r.get('obtenido')
    if 'http' in r:summary=f"HTTP {r['http']}; {r.get('ms')} ms"
    else:summary=cell(actual)
    error='Repetición aplicada dos veces' if r['id']=='P074' else 'No disponible en modelo/API' if r['estado']=='No probado' else '—'
    lines.append('| '+' | '.join(map(cell,[r['id'],r['prueba'],'SIMULADOS',r.get('esperado'),summary,r['estado'],f"pruebas.json #{r['id']}; {error}"]))+' |')
lines.append('''
### Pantallas y regresión

Se recorrieron con Edge las páginas reales de almacén/zonas, productos, inventario,
movimientos, recepciones, órdenes, operarios, proveedores, análisis y monitoreo.
Una primera prueba que verificaba encabezados y ausencia de500 pasó en escritorio;
tras corregir el selector de rack y una espera del menú, el recorrido móvil también
pasó en15,1s. **Esas comprobaciones no acreditaban que Inventario mostrara los datos.**
La revisión de capturas detectó esa cobertura insuficiente y se añadió la aserción
de producto visible en catálogo/inventario/movimientos. La ejecución final falla en
ambos tamaños porque Inventario dice “Aún no hay inventarios”. Es un fallo real de
contrato, no se retiró la aserción para hacer pasar la prueba. Catálogo sí mostró Arroz.
Monitoreo e historial se verificaron en los recorridos previos, con humedad y rack sin
sensores. Evidencias: `desktop-*.png`, `mobile-*.png`, `browser.json` y contexto de error.

Regresión backend después de los cambios: **360 aprobadas, 3 omitidas y 26 subpruebas
aprobadas**, XML `artifacts/piloto.local/regresion-backend.xml`. No se interpreta
esa suite como cobertura completa de la calidad conversacional: esta evaluación
detectó errores que las pruebas previas no cubrían.

## C. Conversación real con Saiki

Se enviaron 46 preguntas a `/saiki/ask`, sin reemplazar Ollama ni inventar respuestas.
Los caminos deterministas devuelven datos del backend y se identifican como tales;
mostrar `model=qwen3:4b` no prueba que cada respuesta haya ejecutado inferencia.
Los timeouts son esperas observadas del cliente, no respuestas redactadas por Saiki.
JSONDecodeError significa que el runner recibió una respuesta no JSON y no pudo
mostrarla; el diagnóstico posterior confirmó HTTP 500 por AttributeError en riesgo.

Algunas duraciones superan la cota de 55 s configurada; por ejemplo 1.384,7 s.
Se registran como tiempo de pared de la sesión con bloqueo/esperas observadas,
no como benchmark controlado ni latencia garantizada del modelo.

| ID | Pregunta real | Respuesta capturada / error | Dato contrastado | Evaluación | ¿Inventó? | Tiempo ms |
|---|---|---|---|---|---|---|
''')
for i,r in enumerate(questions,1):
    answer=r.get('respuesta',{}).get('answer') or ('Sin respuesta utilizable: '+r.get('error','HTTP '+str(r.get('http'))))
    evaluation='Correcta' if i in correct else 'Incompleta / aclaración insuficiente' if i in partial else 'Fallida'
    invented='No demostrado; dato verificado' if i in correct else 'No evaluable: sin respuesta' if r.get('error') else 'Confunde intención o alcance; revisar texto'
    lines.append('| '+' | '.join(map(cell,[f'S{i:02}',r['pregunta'],answer,truth.get(i,''),evaluation,invented,r['ms']]))+' |')
lines.append('''
### Correcciones y repetición de preguntas

1. `saiki_service.py`: se eliminó la condición que convertía cualquier pregunta con
   `id_almacen` en consulta de demanda. La selección del almacén ya no cambia por sí
   sola la intención. Se añadió una prueba de regresión para el conteo de productos.
2. `saiki_intent_router.py`: se reconocen “cómo creo/registro/agrego/veo/consulto/interpreto”.
   Antes se confundían con conteos, sensores o movimientos. Se repitieron las preguntas.
3. `knowledge/psitwin.json`: ayuda empresarial actualizada al registro por enlace
   Gmail y contraseña; se retiraron instrucciones obsoletas de Google OAuth.

Las siguientes respuestas son ejecuciones nuevas, no versiones reescritas a mano:

| Pregunta repetida | Respuesta / error real | HTTP | ms |
|---|---|---|---|
''')
for r in regression:
    lines.append('| '+' | '.join(map(cell,[r['pregunta'],r.get('respuesta',{}).get('answer') or r.get('error',''),r.get('http','—'),r['ms']]))+' |')
lines.append('''
La regresión confirmó la mejora de ayuda y conteo. Las consultas de agotamiento
siguen fallando: `InventoryRiskService.evaluar` llama a
`ForecastService.historial`, que no existe. No se oculta ese fallo ni se fabrican
valores. Una prueba directa de Qwen de 32 tokens también agotó la espera de 15 s
(`ollama_directo.json`). La conversación libre fluida permanece bloqueada en esta evaluación.

## IoT y alertas: qué se comprobó y qué falta

Se registró un dispositivo de temperatura/humedad en C-01. Los límites **solo para
simulación** fueron temperatura2–6 °C y humedad35–65 %, duración0 para provocar
incidentes sin esperar; no son recomendaciones de seguridad alimentaria. Se probaron
normal4/50, alta9/80 repetida, baja1/20, recuperación4/50 y una lectura antigua de
dos horas. Siete lecturas quedaron en MongoDB; no se rellenaron huecos del gráfico.

Se observaron tres incidentes históricos (temperatura, humedad, actualidad), resueltos
al recuperar lecturas. La repetición alta no creó un incidente adicional por el
mismo parámetro. Los eventos reales del backend llegaron a la cola suscrita; esto
prueba producción de eventos ante datos simulados, no una notificación física ni audio.
Saiki consultó historia y dio humedad mínimo20, máximo80 y promedio55 de seis lecturas,
coincidente con los datos. Ante lecturas antiguas no afirmó normalidad actual.

No se probaron sensores físicos, precisión/calibración, cobertura Wi-Fi, caída real
de MQTT, alerta por desconexión en el proceso periódico ni voz proactiva. No se
registró sensor PIR: el modelo actual tiene puerta, que no equivale a movimiento.
La pregunta de movimiento se confundió con movimientos de inventario: fallo semántico.
Se consultaron 1h/24h/7d y fechas explícitas; no se acreditó un historial físico de 7 días.
Los periodos largos contienen únicamente las muestras simuladas existentes.

No se observó alerta automática de stock mínimo/cero al crear los detalles de la
muestra; las tres alertas persistidas eran de sensores. Falta validar/implementar
el disparador de stock para la política operativa deseada. No se acreditó alarma
automática por proximidad de vencimiento; sí recepción con fecha y salida por vencimiento.

## D. Problemas por severidad y acciones previas a operación real

| Severidad | Hallazgo | Evidencia | Acción pendiente |
|---|---|---|---|
| Crítico | Inventario UI vacío con diez detalles en MongoDB | browser.json:2 fallos; captura final y frontend/src/api/inventarios.ts | Adaptar cabecera/detalle en listas, identificadores, filtros, formularios, movimientos e historial; documentar contrato y repetir E2E completo antes de usarlo en tienda |
| Alto | Venta repetida descuenta dos veces | P072–P074, galletas18→16 | Definir clave de idempotencia por empresa/evento, persistir resultado y probar reenvíos y payload distinto; no desplegar doble escritura sin contrato |
| Alto | Riesgo de agotamiento devuelve500 | saiki_regresion.json, AttributeError historial | Restaurar/adaptar historial compartido y probar estado sin historia y con serie válida; no hacer fallback inventado |
| Alto | Demanda operativa suma SALIDA de cualquier motivo, incluido VENCIMIENTO | SerieDemandaRepository.diarios y .primera_salida; ensayo con vencimiento | Separar ventas de merma/vencimiento antes de pronosticar ventas reales; revisar coherencia del artefacto y contrato; cambio documentado, no aplicado silenciosamente |
| Alto | La serie operativa rellena días sin movimiento como cero | AnalisisService.series, values.get(current,0.0) | No interpretar ausencia de registro como cero real sin confirmar integridad diaria; conservar diferencia entre cierre, quiebre y dato faltante |
| Alto | Saiki confunde ajuste, fechas, rack inexistente o sensor sin lecturas | S13,S15,S17,S27,S43,S44 | Filtros explícitos por intención/fecha/ubicación y pruebas contra MongoDB; no usar sus respuestas como registro oficial |
| Alto | Inferencia Qwen no respondió dentro del tiempo observado | S03–S10 y ollama_directo.json | Medir CPU/RAM y perfil de carga, cancelar operaciones reales y validar /events; no prometer tiempo real |
| Medio | Alertas automáticas de stock no acreditadas al crear stock bajo/cero | Snapshot: 3 alertas solo IoT | Definir disparadores y comprobar detección, deduplicación y recuperación |
| Medio | Al reiniciar el monitor no se restauró el último valor al panel en vivo | Captura mobile-sensores.png muestra Sin lecturas mientras el historial sí contiene6 valores | Restaurar última lectura persistida como histórica/desactualizada sin afirmar conexión actual |
| Medio | Catálogo no conserva SKU, precio de venta y unidad comercial dedicados | P055 | Mapeo externo para visita; documentar antes de ampliar DTO/modelo/frontend |
| Medio | Sin transferencia pública ni ajuste/merma/devolución completo | P068–P077 y DTO/controller | Mantener registro externo y no convertirlos en ventas; diseñar trazabilidad antes de habilitar |
| Medio | No se validó producto nuevo con historia suficiente ni exactitud en tienda | P098 + smoke de referencia | Pedir historia diaria, probar serie nueva y backtesting temporal |
| Bajo | Ayuda dependía de verbos en infinitivo y describía OAuth antiguo | S35–S41; regresión | Corregido en esta revisión; ampliar corpus de preguntas |
| Bajo | Avisos proxy WebSocket al navegar e hidratación frontend | Logs del navegador | Revisar cierre de conexiones; recorridos funcionales pasaron tras corregir harness |

No se identificó pérdida de datos entre empresas en los accesos ejercitados; eso
no prueba ausencia de toda vulnerabilidad. No se ejecutaron pruebas destructivas
ni un pentest exhaustivo. Los cambios estructurales se documentaron y quedaron
pendientes; no se reescribió inventario ni el modelo durante una evaluación.

## AutoGluon y datos de tienda

Prueba real local: `verificar_autogluon.py`, Python del entorno aislado, AutoGluon1.6.1,
WeightedEnsemble, frecuenciaD, objetivo cantidad, 1.096 filas de referencia y90 días
de salida con Q10/Q50/Q90. Fuente: runtime_validation.json y smoke_predictions.json
del artefacto local. No se reentrenó ni se afirmó compatibilidad de todos los productos.

El worker construye identificadores y covariables de calendario, valida fechas,
cuantiles y no negatividad. La capa de análisis requiere al menos91 días de cobertura
para su horizonte90 y rechaza huecos importados sin inventar datos. No confundir
cobertura con observaciones reales ni días sin venta con días sin archivo. La fecha
de predicción de referencia comienza después del corte de su dataset, no “hoy en la tienda”.

Para producto nuevo: mapear SKU y almacén, unificar unidad, conservar cierres/quiebres,
preparar serie diaria, comprobar contrato de covariables e inferencia válida y evaluar
con fechas futuras retenidas. AutoGluon puede admitir series nuevas según modelo,
pero **este artefacto debe comprobarse para esa serie**; reentrenamiento no automático.
Pedir12 meses o más, idealmente24–36; con30/60/90 solo hacer las pruebas permitidas
por la cobertura y declarar límites. No adjudicar precisión de referencia a la tienda.
Fuentes: [AutoGluon](https://auto.gluon.ai/stable/tutorials/timeseries/forecasting-indepth.html)
y [validación temporal](https://otexts.com/fpp3/tscv.html).

## E. Datos necesarios, disponibilidad y plantillas

El diccionario completo de la [guía de visita](GUIA_VISITA_TIENDA_PSITWIN.md) incluye
significado, utilidad, rol a consultar, ejemplo, prioridad y fuente de cada dato.
**Todos los datos reales de la tienda están pendientes**; los disponibles hoy son
exclusivamente ejemplos simulados. Resumen para la visita:

| Dato requerido | Ejemplo SIMULADO | Prioridad | Fuente | Módulo | Disponibilidad real |
|---|---|---|---|---|---|
| Catálogo y código estable | PIL-001 arroz1kg | Obligatorio | POS/empaque | Productos/mapeo | Pendiente |
| Conteo físico y saldo registrado con corte |30 físico/32 sistema | Obligatorio | Conteo/POS | Inventario | Pendiente |
| Ubicación y capacidad kg |Principal/secos/B-01 | Obligatorio | Recorrido/ficha | Almacén/Zona/Rack | Pendiente |
| Mínimos/máximos y unidad base |5/100 bolsas | Obligatorio | Encargado | Detalles inventario | Pendiente |
| Ventas diarias y días sin stock/sin datos |8 unidades el26/10 | Obligatorio para demanda | CSV/Excel POS | Análisis | Pendiente |
| Proveedor y plazo de entrega |PROV-01,2 días | Obligatorio reposición | Compras/guías | Proveedor/Órdenes | Pendiente |
| Pedidos y recepciones |20 recibidas | Recomendado | Guía/orden | Recepciones/Movimientos | Pendiente |
| Lotes y vencimientos |L01, fecha impresa | Obligatorio si perecible | Empaque/recepción | Recepciones | Pendiente |
| Sensor y límites documentados |ID, unidad, fuente | Obligatorio si IoT | Técnico/fabricante | Monitoreo/Alertas | Pendiente |
| Permisos y roles |Encargado recibe | Obligatorio | Dueño | Accesos/piloto | Pendiente |
| Precios, promociones y pérdidas |S/4, campaña | Opcional/recomendado | POS/entrevista | Evaluación externa | Pendiente |

Excel y seis CSV con ejemplos SIMULADOS: `docs/plantillas_tienda/`. Incluyen catálogo,
stock, ventas, proveedores, reposición y movimientos, con significado de todas las
columnas en LEEME.md. No son un importador universal; no se prometió esa capacidad.

## F. Entrevista y G. Visita

Usa [Preguntas para el dueño](PREGUNTAS_DUENO_TIENDA.md), 41 preguntas en lenguaje
sencillo; [Checklist](CHECKLIST_DATOS_TIENDA.md) para recibido/pendiente/no aplica;
y la [agenda de60–90min](GUIA_VISITA_TIENDA_PSITWIN.md), con permisos, recorrido,
conteo, exportación, demostración, sensores y cierre. El dueño debe validar tres
problemas y sus criterios de mejora antes de decidir si continúa el piloto.

## H. Conclusión y cómo probarlo

1. **¿Listo?** No para piloto operativo ni demo completa de Inventario en la UI.
   Sí para levantar datos, catálogo/monitoreo y demostración parcial por API en copia.
2. **Funciona:** autenticación por enlace/contraseña, roles, estructura física,
   catálogo por proveedor, stock por rack, recepción, venta y vencimiento,
   persistencia, concurrencia ensayada, ingesta simulada e historial IoT.
3. **Reparar antes de operar:** contrato inventario frontend/backend, idempotencia de venta, riesgo sin historial,
   semántica/filtros de Saiki, definición de demanda vs salidas y disparadores de stock.
4. **Mínimos a recoger:** permisos,10 productos con unidad/código, ubicación,
   conteo con corte, mínimos/máximos, proveedor/lead time y archivos diarios disponibles.
5. **Ideal para pronóstico:**12–36 meses diarios con cierres, quiebres, promociones,
   devoluciones y unidades consistentes; validación temporal sin fuga de información.
6. **Demostración inmediata:** catálogo y monitoreo UI; inventario/recepción/venta
   solo por API controlada en copia hasta adaptar el frontend. Sensores SIMULADOS
   identificados. Usar solo preguntas de Saiki ya contrastadas.
7. **Requiere historia/hardware:** inferencia nueva validada, precisión en tienda,
   calibración, MQTT/red reales y avisos hablados físicos no comprobados aquí.
8. **Riesgos:** doble venta al reintentar, datos fuente incompletos, mezclas de unidades,
   tiempos del LLM, consultas fuera de intención, límites IoT no documentados y permisos.

Desde Git Bash, raíz del proyecto:

```bash
./iniciar.cmd -Detener
./iniciar.cmd
# Aplicación habitual: http://localhost:5173
```

Para repetir QA, exclusivamente con una base nueva SIMULADA:

```bash
./.runtime.local/python/python.exe backend/scripts/evaluar_piloto.py
cd frontend
npm.cmd exec -- playwright test --config playwright.piloto.config.ts
cd ..
./.runtime.local/python/python.exe backend/scripts/cerrar_evaluacion_piloto.py
```

El primer script crea una base aislada nueva y conserva evidencias; las46 preguntas
pueden tardar y mostrar fallos reales. No ejecutes múltiples runners simultáneamente.
El navegador de piloto usa15174/18081, no la API productiva. El manifiesto contiene
credenciales **solo SIMULADAS** para esa base, nunca las de la tienda.

Después de guardar la evidencia y cerrar el navegador piloto, revierte únicamente
su base con el comando comprobado por prefijo y UUID:

```bash
./.runtime.local/python/python.exe backend/scripts/evaluar_piloto.py --cleanup
```

No uses dropDatabase contra la base normal. Los snapshots permiten revisar el
estado aun después de limpiar. Las plantillas y documentos permanecen en docs.

Archivos de implementación corregidos: `backend/app/services/saiki_service.py`,
`saiki_intent_router.py`, `backend/app/knowledge/psitwin.json` y prueba de regresión
`backend/tests/test_saiki_demand_analysis.py`. Se añadieron runners, servidor y
configuración de navegador exclusivos del piloto. No se cambiaron los contratos
de movimientos, AutoGluon ni los datos de producción para ocultar hallazgos.
''')
if (ROOT/'docs/CORRECCION_INVENTARIO_FRONTEND.md').exists():
    lines.insert(0, '> Evaluación histórica: el bloqueo de inventario vacío tiene una corrección posterior. Consulta [corrección y pruebas](CORRECCION_INVENTARIO_FRONTEND.md). Los resultados originales se conservan como evidencia.\n')
(ROOT/'docs/INFORME_PRUEBAS_INTEGRALES_PSITWIN.md').write_text('\n'.join(lines),encoding='utf-8')
print('Informe generado desde evidencia:',len(checks),'comprobaciones,',len(questions),'preguntas,',len(regression),'repeticiones')
