# Validación iterativa de Saiki

## Actualización: entorno autorizado y validación completa

Se preparó `venv/saiki-tests-py312`, ignorado por Git, con Python portátil
3.12.2 oficial. Se copiaron únicamente las dependencias necesarias y su cierre
transitivo desde .venv; se añadieron HTTPX, HTTPcore y certifi para probar HTTP.
El manifiesto de paquetes copiados está en el propio entorno. El intérprete
usa rutas explícitas aisladas; no modifica PATH ni instala Python globalmente.
.venv, .env y las claves permanecen intactos.

Resultado final: **105 pruebas y 26 subcasos aprobados en 17,05 segundos**.
Incluye las suites Saiki, aislamiento, notificaciones y rack, las pruebas
HTTP nuevas y la evaluación nativa de LightGBM.

Las pruebas HTTP utilizan FastAPI, DTO, JWT criptográfico, AccesoService,
herramientas y repositorios reales. Solo la persistencia se sustituye por
colecciones sintéticas, sin operaciones de escritura implementadas. La app
de prueba no incluye el lifespan de producción. Se probaron tokens ausentes,
malformados, expirados y con firma incorrecta; referencias ajenas aportadas
por cliente o modelo; contexto manipulado; roles privilegiados en historial;
y concurrencia entre empresas para inventario, alertas, recomendaciones y
movimientos. No se reemplazaron claves: los tokens de prueba se generan en
memoria y no se registran.

El forecast HTTP ejecutó el constructor de características y los siete modelos
reales con historial/contexto sintéticos. Se comprobaron siete resultados,
ventana histórica de treinta días, fuentes y advertencias de variables faltantes.
La medición conversacional de InventoryRisk sustituye el evaluador por un
resultado sintético; no valida sus fórmulas ni altera su implementación.

## Fallos encontrados y corrección iterativa

La consulta de ubicación con Ollama real agotó la lectura: HTTP 504 después de
180029,02 ms, una inferencia de 180009,49 ms y ninguna herramienta ejecutada.
Se conserva la evidencia en `venv/saiki-tests-py312/real-ollama-before.json`.
No se aumentó el timeout ni se cambiaron opciones del modelo.

Se añadió resolución directa de ubicaciones claramente identificables con
catálogo filtrado por empresa. Si no hay coincidencia informa que no encontró
el producto; si hay varias pide aclaración; si hay una usa ubicaciones reales
visibles y conserva los datos estructurados. Preguntas complejas siguen al
loop. Se probaron producto ubicado, producto sin ubicación y coincidencias
múltiples, además de la exclusión del catálogo ajeno.

La misma consulta con el mismo catálogo sintético pasó posteriormente con
HTTP 200, 7,13 ms y cero inferencias. Esto demuestra que ese camino evita el
modelo; **no demuestra recuperación del rendimiento de Ollama para preguntas
complejas ni latencia equivalente con MongoDB real**.

El arnés AST requirió importar `re` tras incorporar la búsqueda de nombres.
Ese fallo se corrigió y toda la suite se repitió hasta aprobar. Durante la
preparación hubo errores de ruta de importación y faltaba h11: se corrigieron
solo las rutas y dependencias del entorno separado, sin modificar .venv.

## Medición final y reproducción

SAIKI_VALIDACION_MEDICIONES.json contiene las doce solicitudes HTTP, sus tiempos
de clasificación/herramientas, llamadas simuladas y evidencia antes/después de
ubicación. Seis preguntas sencillas usan cero inferencias. Las otras seis usan
dos inferencias simuladas: su tiempo no representa una evaluación real de Qwen.
MongoDB real permanece como no medido; no se presenta como tiempo cero.

Desde la raíz, en PowerShell:

```powershell
$env:EMAIL_ENABLED = 'false'
$env:MONGODB_URL = 'mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=100'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:SAIKI_REAL_OLLAMA_TEST = '1'
& .\venv\saiki-tests-py312\python.exe -B -m pytest tests -q -p no:cacheprovider
```

Estas variables afectan exclusivamente al proceso de prueba, no a .env. La
prueba opt-in actualmente verifica que la ubicación sencilla evita Ollama.
El fallo de inferencia real anterior se conserva como antecedente y no se
reclasifica como una inferencia satisfactoria.

Pendientes: medición con MongoDB de prueba aislado, rendimiento del modelo
para preguntas complejas, servidor de producción y frontend real. No hay
autorización para escribir en datos reales ni para corregir aliases JWT.

---

Las secciones siguientes documentan las etapas anteriores; los bloqueos de
entorno allí descritos quedaron superados por la preparación autorizada.

## Alcance y resultados

- 16 pruebas de aislamiento/routing/respuestas aprobadas en
  test_saiki_isolation_stdlib.py. Se ejecutan métodos reales extraídos mediante
  AST; frameworks, autorización y persistencia se sustituyen por colaboradores
  simulados. Incluyen cuatro herramientas concurrentes entre empresas,
  catálogo, identificador ajeno y fallo simulado del decodificador JWT.
- El test de regresión ejecuta las seis pruebas originales de rack contra la
  regla real extraída del servicio, evitando imports FastAPI. No es integración.
- Un test nativo LightGBM aprobado: siete pesos globales reales, DLL existente,
  métodos reales predict_horizon/predict_7_days, características sintéticas
  faltantes. Inferencia de siete días: 11,779 ms inicialmente y 5,381 ms en una
  ejecución posterior, excluyendo carga de modelos. No prueba la exactitud ni
  el pipeline MongoDB/contexto/features. Horizontes 0, 8 y 30 rechazados.
- Doce preguntas ejecutadas con herramientas y Ollama simulados. Cinco usan
  cero llamadas al modelo; siete recorren dos llamadas simuladas. Estos tiempos
  no demuestran latencia inferior a cinco segundos en producción.
- Medidas por pregunta en SAIKI_VALIDACION_MEDICIONES.json: tiempo total del
  servicio incluyendo asyncio.run, clasificación medida separadamente,
  ejecución del colaborador de herramienta y tiempos de inferencias falsas.
  MongoDB figura como null, nunca como cero medido. El constructor del servicio
  y la carga de modelos no están incluidos en el tiempo por pregunta.

## Correcciones mínimas

1. Proyección no coincidía con el término proyectar: se añadió la raíz proyecc.
2. Demanda de la próxima semana quedaba ambigua: se reconoce el horizonte junto
   a demanda. Se conserva la interpretación de demanda, no de stock futuro.
3. Conteo de productos, existencia de almacenes y stock total iban al modelo:
   ahora tienen rutas directas; preguntas con calificadores siguen al modelo.
4. El conteo de catálogo no debe deducirse de inventarios o almacenes: get_product
   admite ID opcional. Con ID conserva su respuesta anterior; sin ID devuelve
   catálogo filtrado por empresa. Esta variante devuelve lista y se añade al
   contrato de herramientas; data conserva su estructura externa por herramienta.
5. Se añade total_almacenes al resumen, incluyendo almacenes sin stock.
6. Alertas específicas incluían estados resueltos: get_active_alerts filtra ACTIVA,
   coherente con la consulta global existente; VISTA no se incorpora como ACTIVA.
7. La respuesta estructurada advierte cuando el forecast reporta variables
   sin datos. No se alteraron fórmulas, características o pesos del modelo.
8. Clasificación medida una sola vez y registrada separadamente.

## Servicios reales

Ollama /api/tags respondió HTTP 200 y confirmó qwen3:4b instalado. No se lanzó
ninguna inferencia real Ollama. Dos consultas con localhost tardaron 2079,052 y
2058,867 ms; con 127.0.0.1 tardaron 18,920 y 22,558 ms. Es una observación de
conectividad desde este intérprete, no diagnóstico confirmado de los 120 s.
No se cambió la configuración ni se atribuyó el efecto a una causa concreta.

FastAPI no respondió en localhost:8000 al intento con token sintético inválido.
Por tanto, JWT real, DTO/serialización HTTP y latencia del endpoint siguen
pendientes. No se inició la aplicación contra MongoDB: el lifespan crea índices.
No se utilizó información real de otras empresas ni se modificó MongoDB.

## Entorno y pendientes

.venv referencia Python312/python.exe, que no puede utilizarse desde esta sesión.
El Python 3.11 de Inkscape funciona y permite la suite sin dependencias y la DLL.
Los binarios cp312 no sirven para importar las dependencias en Python 3.11.

test_saiki_service.py no pudo arrancar: .venv no encuentra su Python base;
Python 3.11 no tiene pytest. Las regresiones completas de notificaciones y rack
no importan por ausencia de pydantic_settings y fastapi respectivamente.
Son bloqueos de entorno, no casos funcionales aprobados ni fallos de lógica.

Pendiente autorizar un entorno separado para pytest/FastAPI/Pydantic, ejecutar
pruebas de integración con datos exclusivamente sintéticos y medir MongoDB y
el endpoint real. No se instalaron paquetes ni cambiaron JWT, .env o entornos.
No se realizó commit/push ni se revirtieron cambios locales anteriores.
