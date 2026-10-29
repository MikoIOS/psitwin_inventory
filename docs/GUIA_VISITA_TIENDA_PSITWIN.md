> Actualizacion: el bloqueo de inventario vacio fue corregido y probado. Consulta [Correccion del inventario](CORRECCION_INVENTARIO_FRONTEND.md). El resto del informe conserva los resultados historicos y los demas hallazgos pendientes.

# Guía para visitar la tienda y preparar el piloto de PsiTwin

Fecha de preparación: 27 de octubre de 2026, hora de Lima. Los ejemplos de esta
guía son **SIMULADOS**. Ningún ejemplo representa a la tienda que visitarás.

## Alcance y decisión antes de salir

La primera visita debe ser una demostración supervisada y un levantamiento de
información, con **10–20 productos** representativos. Mantén el sistema o cuaderno
actual como registro oficial. No sustituyas su operación con PsiTwin hasta resolver
los hallazgos del [informe de pruebas](INFORME_PRUEBAS_INTEGRALES_PSITWIN.md).

**Bloqueo actual:** Inventario en la interfaz muestra vacío aunque la API y MongoDB
tengan existencias. El frontend y backend usan contratos distintos de cabecera y
detalle. Antes de prometer una demo completa de venta/inventario por pantalla,
debe adaptarse esa integración y pasar el E2E. Mientras tanto limita la visita al
levantamiento, catálogo/monitoreo y una demo técnica por API en copia; los pasos
operativos de esta guía son el plan a ejecutar después de resolver ese bloqueo.

Prioriza dos productos de alta rotación, dos que se agoten, dos de baja rotación,
dos refrigerados o perecibles y dos con reposición difícil. Si no venden refrigerados,
adapta la selección; no instales sensores sin una necesidad real.

En el código revisado, la empresa administra almacenes, zonas, racks y accesos;
el **proveedor crea los productos** y el **operario registra las salidas y recibe
mercadería**. Prepara cuentas de demostración para esos tres roles. No prometas
que el dueño podrá cargar el catálogo directamente desde su cuenta empresarial.

## Permisos y tratamiento de datos

Pide autorización al dueño o responsable para: usar los datos seleccionados,
exportar archivos, realizar un conteo, crear una copia de prueba, conectar equipos,
usar la red y tomar fotografías. Cada permiso es independiente. Anota responsable,
fecha, finalidad, duración del piloto, quién accede, plazo de conservación y cómo
se devolverán o eliminarán las copias. Una negativa a fotografías no impide el piloto.

No solicites contraseñas de Gmail, del sistema de caja, de bancos ni de cuentas
personales. El dueño introduce su contraseña de PsiTwin y abre su correo por sí
mismo. Para Wi-Fi usa una red de invitados autorizada; no guardes la clave en el
informe. Solicita exportaciones de **productos y cantidades**, sin nombres de
clientes, DNI, tarjetas ni detalles de pagos. Sustituye nombres de empleados por roles.

El formulario actual exige RUC, Gmail, nombre CEO y teléfono para una cuenta nueva.
Para una demostración usa la empresa SIMULADA aislada; no pongas un RUC inventado
como si fuera el de la tienda ni registres a una persona sin permiso. El catálogo y
las ventas pueden anonimizarse con códigos estables. Precios y datos tributarios
pueden omitirse del levantamiento inicial si solo se probarán unidades y stock;
los campos que exige el formulario real requieren consentimiento o una cuenta de demo.

## Qué llevar y qué preparar

- Laptop cargada, cargador, extensión autorizada, mouse y respaldo de energía si existe.
- Frontend, FastAPI y MongoDB probados; `./iniciar.cmd` desde Git Bash.
- Ollama con `qwen3:4b` descargado y una consulta corta ensayada; chat escrito como respaldo.
- Entorno AutoGluon, artefacto y pesos locales ya disponibles. No depender de descargas en la tienda.
- Base aislada, cuentas SIMULADAS por rol, copia de seguridad y procedimiento de limpieza.
- Esta guía, entrevista, checklist y plantillas; una hoja impresa de conteo si no hay Excel.
- CSV de ejemplo, capturas de respaldo y un video corto si falla la conexión.
- Si hay permiso: sensores identificados, fuente de alimentación y un instrumento
  de referencia adecuado. Registra modelo, unidad y fecha de calibración conocida.
- Internet para Gmail SMTP y recibir el enlace de activación. Voz, OAuth y servicios
  de pago no son necesarios para demostrar inventario. No dependas de Google OAuth.

Comprueba antes de ir: login/logout, un producto, un movimiento, stock final,
una lectura, historial y una pregunta de Saiki que haya pasado la revisión. Define
un responsable de la prueba y otro de la tienda que valide los conteos.

## Diccionario de información que debes pedir

Prioridades: **O** obligatorio para el escenario elegido; **R** recomendado;
**Op** opcional. Todo está **pendiente de obtener de la tienda**. Un dato opcional
no debe bloquear el piloto. “Externo” significa que conviene levantarlo aunque el
modelo actual de PsiTwin no lo almacene en ese módulo. Usa las plantillas como
captura; no equivalen a un importador automático de todos los módulos.

| Dato y significado | Para qué / módulo real | Preguntar a | Ejemplo SIMULADO | Prioridad | Fuente posible |
|---|---|---|---|---|---|
| Nombre comercial: identificación del negocio | Contexto y empresa | Dueño | Bodega Demo | O | Entrevista |
| Rubro / sector | Empresa y selección de productos | Dueño | Abarrotes | O | Entrevista |
| Número de locales | Delimitar alcance y evitar mezclar sucursales | Dueño | 1 local | R | Entrevista |
| Almacenes existentes | Crear estructura real | Encargado | Sala y depósito | O | Recorrido |
| Horarios de atención | Interpretar días incompletos y actividad | Encargado | 08:00–21:00 | R | Entrevista/cartel |
| Días abiertos y cierres excepcionales | Diferenciar cero ventas de local cerrado | Encargado | Lunes a sábado | O para demanda | Calendario/entrevista |
| Responsable de inventario, por rol | Validar datos y permisos | Dueño | Encargado de almacén | O | Entrevista |
| Método actual de control | Elegir exportación o conteo | Encargado | Excel semanal | O | Sistema/cuaderno |
| Uso de códigos de barras | Construir correspondencia de productos | Cajero | EAN en empaques | R | Empaques/POS |
| Problemas actuales | Elegir 3 objetivos medibles | Dueño | Quiebres, vencimientos, conteo lento | O | Entrevista |
| SKU: código estable de producto/presentación | Mapeo externo a id_producto; no hay SKU comercial dedicado en DTO revisado | Encargado | PIL-001 | O | POS/Excel/etiqueta |
| Nombre de producto | Catálogo, búsqueda y Saiki | Encargado/proveedor | Arroz 1 kg | O | Etiqueta/catálogo |
| Marca | Campo marca de producto | Encargado | Marca Demo | R | Empaque |
| Categoría y familia | Campos de catálogo y filtros | Encargado | Granos / abarrotes | O | Catálogo/entrevista |
| Presentación | Evitar mezclar tamaños; conservar en nombre o mapeo externo | Encargado | Bolsa 1 kg | O | Empaque |
| Unidad base de conteo | Stock entero actual; acordar unidad vendible | Encargado | Bolsa | O | POS/empaque |
| Unidades por caja o paquete | Convertir compras a unidad base; externo | Proveedor | 12 bolsas/caja | O si compra por caja | Factura/empaque |
| Peso por unidad en kg | Campo obligatorio peso; capacidad de racks | Proveedor/encargado | 1 kg/unidad | O | Etiqueta/balanza |
| Volumen por unidad | Campo opcional volumen | Proveedor | 0.001 m³ | Op | Ficha técnica |
| Precio de compra y moneda | Costo de línea de reposición; no precio de catálogo dedicado | Dueño/compras | S/ 3.20 | R | Factura/POS |
| Precio de venta | Evaluación comercial externa; no campo de catálogo revisado | Dueño | S/ 4.00 | Op | POS/entrevista |
| Proveedor habitual y código | Relación proveedor-producto y órdenes | Compras | PROV-01 | O | Facturas/catálogo |
| Vida útil en días | Campo de producto; no sustituye vencimiento real del lote | Proveedor | 180 días | O en catálogo actual | Fabricante |
| Requiere refrigeración | Validar producto y ubicación | Proveedor | Sí | O | Etiqueta/ficha técnica |
| Vencimiento por lote | Recepción/lotes, no fecha única inventada del producto | Encargado | Lote L01, 2026-11-15 | O si aplica | Etiqueta/recepción |
| Ubicación actual por producto | Detalle inventario por rack | Almacenero | Depósito / secos / B-01 | O | Recorrido/conteo |
| Stock físico: unidades observadas | Línea base independiente | Almacenero y evaluador | 30 bolsas | O | Conteo firmado |
| Stock registrado: saldo del sistema actual | Conciliar diferencias | Encargado | 32 bolsas | O | POS/Excel/cuaderno |
| Stock reservado: comprometido | Calcular disponible externamente; no asumir campo nativo | Encargado | 2 bolsas | R | Pedidos/entrevista |
| Stock disponible | Físico utilizable menos reservas/bloqueos; derivar con tienda | Encargado | 28 bolsas | R | Conteo y reservas |
| Stock mínimo | Umbral por ubicación de inventario | Encargado | 5 unidades | O | Política/entrevista |
| Stock máximo | Campo obligatorio del detalle actual y límite de validación | Encargado | 100 unidades | O | Capacidad/política |
| Stock de seguridad | Contexto de reposición, externo si no está modelado | Compras | 8 unidades | R | Política/estimación marcada |
| Agotados y fechas de quiebre | Separar ventas observadas de demanda censurada | Cajero/encargado | Sin stock del 10 al 12 | O para demanda | POS/registro/entrevista |
| Próximos a vencer | Caso perecible y lotes por revisar | Almacenero | 3 yogures, lote L02 | R | Etiqueta/conteo |
| Dañados, vencidos o bloqueados | Evitar venderlos y clasificar mermas externamente | Almacenero | 2 envases dañados | O si hay | Acta/conteo |
| Fecha y hora del último conteo | Corte de conciliación | Encargado | 2026-10-27 09:00 Lima | O | Acta/Excel |
| Ventas por fecha y producto, en unidades | Serie histórica diaria para demanda | Administrador POS | PIL-001, 2026-10-01, 8 | O para pronóstico | CSV/Excel de POS |
| Identificador de venta o agregado diario | Deduplificar y auditar fuente | Administrador POS | V-001 o agregado único | O | POS/boletas anonimizadas |
| Rango histórico y meses disponibles | Evaluar suficiencia y estacionalidad | Dueño/POS | 12 meses | O | Exportación |
| Ventas semanales/mensuales | Conciliar agregados diarios; no duplicar importación | Dueño | 60/240 unidades | R | Reportes de ventas |
| Días de mayor venta | Comparar con patrón calculado, no reemplazar serie | Encargado | Sábado | R | POS/entrevista |
| Temporadas y eventos | Contexto para interpretación; solo covariables admitidas van al modelo | Dueño | Campaña escolar | R | Calendario/promociones |
| Promociones y descuentos por fecha | Interpretar picos, no inventar causalidad | Dueño | 2×1 el 15/10 | R | POS/cartel |
| Devoluciones de clientes | Separarlas de ventas brutas y recepciones | Cajero | 1 unidad el 16/10 | O si aplica | POS/notas de crédito |
| Días sin datos vs cero ventas | No rellenar huecos como cero sin evidencia | Administrador POS | 02/10 archivo ausente | O | Conciliación de archivos |
| Ventas perdidas estimadas | Registro separado de demanda no satisfecha, con método | Dueño | 3 consultas sin stock | Op | Anotación/entrevista |
| Frecuencia de reposición | Tiempo entre compras, distinto del plazo de entrega | Compras | Cada 7 días | O | Historial de compras |
| Cantidad habitual de compra | Decisiones de reposición | Compras | 2 cajas | O | Factura/pedido |
| Fecha de detección y fecha de pedido | Medir demora interna antes de ordenar | Encargado | Lunes detecta, martes pide | R | Registro/entrevista |
| Lead time: pedido a recepción | lead_time_dias del producto/proveedor | Compras/proveedor | 2 días | O | Fechas de pedido y recepción |
| Plazo mínimo y máximo real | Variabilidad del proveedor | Compras | 1–4 días | R | Historial de recepciones |
| Pedido mínimo y múltiplo de caja | Restricciones comerciales externas | Proveedor | 1 caja, 12 unidades | R | Lista de precios |
| Visitas y días de entrega | Planificar reposición | Proveedor | Martes y viernes | R | Acuerdo/entrevista |
| Costo de envío | Evaluación comercial externa | Compras | S/ 10/pedido | Op | Factura |
| Proveedores alternativos | Contingencia del piloto | Dueño | PROV-02 | Op | Entrevista |
| Pedidos pendientes y retrasados | No recomendar compras duplicadas | Compras | 20 unidades, demora 1 día | O si hay | Órdenes/Excel |
| Historial de compras y recepciones | Validar recepción, costos y lead time | Compras | Pedido 01 y guía 01 | R | Factura/guía/Excel |
| Entradas y sus documentos | Orden y recepción generan entrada real | Almacenero | Recepción 20 unidades | O | Guías/recepciones |
| Salidas por venta | Movimiento SALIDA/VENTA actual | Cajero/operario | Venta 8 unidades | O | POS/registro |
| Transferencias | Trazabilidad requerida, sin endpoint actual; registrar externamente | Almacenero | B-01 a A-01: 5 | R si ocurre | Hoja de traslado |
| Mermas y pérdidas | Distinguir de venta; API pública actual no acepta MERMA | Encargado | Envase roto, 1 | O si ocurre | Acta/cuaderno |
| Vencimientos | SALIDA/VENCIMIENTO disponible | Almacenero | 1 unidad vencida | O si ocurre | Etiqueta/acta |
| Ajustes por conteo y devoluciones | Levantar evidencia; no hay flujo público completo de ajuste/devolución | Encargado | Sistema 32, físico 30 | R | Conteo/nota |
| Nombre, coordenadas, área, aforo y tipo de almacén | Campos obligatorios actuales de Almacén | Encargado | Depósito, 40 m², 8 personas | O para cargar almacén | Recorrido/plano |
| Zonas, refrigeración y número de niveles | Campos de Zona y límite de racks | Almacenero | Secos, 2 niveles | O | Recorrido |
| Código, nivel y capacidad kg de rack | Rack; capacidad es carga, no número de unidades | Encargado | B-01, nivel 1, 100 kg | O | Etiqueta/fabricante |
| Productos por ubicación y niveles | Evitar inventario duplicado por ubicación | Almacenero | Arroz en B-01 | O | Conteo/plano |
| Espacios refrigerados y capacidad | Asignación coherente de perecibles | Encargado | Vitrina 1 | O si aplica | Recorrido/ficha técnica |
| Permiso de fotos o plano | Evidencia espacial | Dueño | Plano sí, fotos no | O antes de capturar | Autorización |
| Sensores existentes: modelo, ID y variable | Dispositivos y compatibilidad de payload | Técnico | ESP32 + temperatura | O si hay | Etiqueta/configuración |
| Variable a medir y ubicación exacta | Monitoreo por rack | Encargado/técnico | Temperatura en C-01 | O para IoT | Recorrido/entrevista |
| Unidad, intervalo y zona horaria | Comparar historial correctamente | Técnico | °C, cada 30 s, Lima | O para IoT | Configuración |
| Origen de límites mínimo/máximo | Configuración fundamentada; no inventar seguridad alimentaria | Proveedor/responsable | Ficha técnica del producto | O antes de alertar | Documento del fabricante |
| Límite normativo aplicable, si corresponde | Registrar referencia y validación responsable, sin sustituir asesoría | Responsable de calidad | Norma y versión verificadas | R/según producto | Documento oficial |
| Límite operativo de la tienda | Separar preferencia operativa de norma/fabricante | Encargado | Umbral interno documentado | R | Política escrita |
| Acción, destinatario y tiempo ante alarma | Diseñar respuesta útil | Dueño/encargado | Revisar equipo y registrar acción | O para IoT | Acuerdo operativo |
| Wi-Fi, electricidad y permisos de equipos | Viabilidad física | Dueño/técnico | Red invitados y toma disponible | O para IoT | Prueba autorizada |
| Movimiento físico necesario | Confirmar necesidad; el módulo actual tiene puerta, no PIR genérico | Dueño | No requerido | Op | Entrevista |
| Instrumento de referencia y calibración | Evaluar exactitud, no solo transmisión | Técnico | Termómetro identificado | R para IoT | Certificado/ficha |
| Quién crea productos | Acceso proveedor y catálogo | Dueño | Proveedor autorizado | O | Matriz de roles |
| Quién recibe, vende y cuenta | Acceso operario; responsabilidades reales | Dueño | Operario de turno | O | Entrevista |
| Quién autoriza compras y ajustes | Aprobación empresa; ajustes aún limitados | Dueño | Encargado | O | Procedimiento |
| Quién revisa alertas y necesita acceso | Permisos mínimos y atención | Dueño | Encargado de frío | O | Acuerdo por roles |
| Tiempo actual de conteo y pérdidas conocidas | Línea base para medir beneficio | Dueño | 45 min, 2 faltantes/semana | R | Medición/actas |

## Cómo preparar archivos y un catálogo sin SKU

Asigna códigos estables `PIL-001`, `PIL-002` por combinación producto–marca–tamaño.
Una botella de 500 ml y otra de 1 L son productos distintos. Conserva una tabla de
equivalencias SKU origen → código piloto → `id_producto` generado por PsiTwin.
No uses nombres que cambien cada semana como clave. No reutilices códigos eliminados.

Cuenta en una unidad base explícita. Si compra dos cajas de 12, la entrada es 24
unidades vendibles. **El stock actual usa enteros**; productos vendidos por peso
fraccionario necesitan una unidad base acordada o adaptación, no redondeo oculto.
El peso del catálogo es kg por unidad para calcular carga del rack.

Pide CSV UTF-8 o Excel sin contraseñas, una fila por dato, fechas `AAAA-MM-DD`,
cantidades numéricas y moneda explícita. No mezcles totales semanales con filas
diarias. Para varias sucursales agrega local/almacén. Verifica duplicados, fecha
inicial/final y total de unidades contra el reporte original antes de importar.
Guarda el archivo original intacto y trabaja sobre una copia.

Las plantillas adjuntas son para **levantar y conciliar** datos. El sistema tiene
importación específica de demanda; no se verificó un importador universal de
catálogo/stock/proveedores. No prometas que cualquier Excel se cargará con un clic.

## Ventas e interpretación del pronóstico

Pide primero ventas **diarias reales por producto**, no solo el promedio recordado.
Ideal: 12 meses o más; 24–36 meses permiten comparar más de un ciclo anual. Esta
es una meta de levantamiento, no una garantía automática de precisión.

| Historia disponible | Qué puedes hacer | Qué no debes afirmar |
|---|---|---|
| 30 días | Conciliar ventas, estudiar calidad y mostrar catálogo/stock/movimientos | Estacionalidad anual ni pronóstico validado; el servicio exige más historia |
| 60 días | Revisar patrón semanal preliminar y quiebres documentados | Precisión estable o compatibilidad garantizada con el artefacto |
| 90 días | Preparar series y evaluar faltantes; revisar el umbral exacto del runtime | Que 90 filas siempre habiliten inferencia; la API actual exige al menos 91 días |
| 12 meses | Evaluación con cortes temporales y comparación con una referencia simple | Que una única inferencia ya mida precisión futura |
| 24–36 meses | Contrastar campañas y patrones anuales, si la calidad lo permite | Que el pasado elimine incertidumbre o quiebres de stock |

En este proyecto AutoGluon usa frecuencia diaria, objetivo `cantidad`, horizonte
90 días y covariables de calendario generadas por el worker. No se reentrena
automáticamente con un producto nuevo. Revisa identificadores, frecuencia,
continuidad, valores no negativos, unidades y contrato de covariables. Prueba primero
una serie nueva en la base de piloto y valida su salida; reentrena solo si el
artefacto no es compatible o el desempeño local lo justifica, con autorización.

No conviertas un día sin archivo en cero. Un día cerrado, cero ventas con stock,
stock agotado y datos faltantes son situaciones distintas. Una venta no mide la
demanda que no pudo atenderse. Mantén estimaciones de ventas perdidas separadas y
con su método. Reserva fechas posteriores al entrenamiento para medir errores;
no evalúes precisión usando únicamente datos que ya vio el modelo.
Referencias: [contrato de series AutoGluon](https://auto.gluon.ai/stable/tutorials/timeseries/forecasting-indepth.html)
y [validación temporal](https://otexts.com/fpp3/tscv.html).

## Demostración paso a paso

1. Explica que trabajarás en una copia o empresa de piloto y confirma los permisos.
2. Elige los productos y fija fecha/hora de corte. Cuenta antes de registrar ventas.
3. Como empresa crea Almacén; abre sus zonas y crea racks respetando niveles y kg.
4. Prepara proveedor y operario; cambia sus contraseñas temporales. El dueño no
   comparte credenciales personales contigo.
5. Como proveedor registra productos y atributos que existan. Guarda SKU, precios
   de venta y campos aún no soportados en la plantilla externa.
6. Como operario asigna rack y crea los detalles de stock inicial; valida mínimos,
   máximos y peso. Conserva el acta de conteo como evidencia.
7. En una **copia SIMULADA**, registra una SALIDA/VENTA de 8 sobre 50: espera 42.
   En operación real, solo registra una venta efectivamente realizada y autorizada.
8. Para entrada crea solicitud/orden con línea, la empresa valida y el operario
   registra recepción. No uses una venta negativa para simular recepción.
9. Consulta Movimientos e Historial y contrasta con MongoDB/reporte de control.
10. Con permiso conecta un dispositivo al rack y configura límites documentados.
    Si no hay equipo, usa lecturas SIMULADAS en la base de demo y anúncialo claramente.
11. Genera una alerta controlada en el simulador, no calentando alimentos ni
    desconectando equipos reales. Comprueba incidente, rack, fecha y recuperación.
12. Pregunta a Saiki conteo, ubicación y sensores. Contrasta siempre con pantalla
    y datos. Si tarda o responde otra cosa, registra el fallo y continúa por módulos.
13. Muestra análisis histórico y el estado sin historial. Usa el resultado de
    referencia de AutoGluon como **demostración técnica**, no como venta esperada de la tienda.
14. Recuenta: saldo final = inicial + entradas − ventas − otras salidas autorizadas.
    Conciliar por producto y ubicación; no sumar indiscriminadamente unidades distintas.
15. Pide comentarios, confirma los tres problemas principales y acuerda próximos pasos.

**Precauciones específicas detectadas:** repetir una venta puede descontar otra
vez; no reenvíes ante una pantalla lenta sin consultar primero el historial.
Las recepciones duplicadas se rechazan. No hay transferencia pública completa ni
flujo público completo de merma/ajuste/devolución; no los disfraces como ventas.
Puerta abierta/cerrada no equivale a un sensor de movimiento PIR.

## Agenda de visita de 60–90 minutos

| Minutos | Actividad | Resultado que debes obtener |
|---|---|---|
| 0–10 | Presentación, permisos, alcance y 3 problemas | Autorización y objetivos escritos |
| 10–20 | Recorrido y mapa de almacén/zonas/racks | Ubicaciones y responsables |
| 20–35 | Elegir 10–20 productos y conteo de muestra | Catálogo y stock con corte |
| 35–45 | Revisar exportación de ventas y reposición | Archivo o compromiso de entrega, rango histórico |
| 45–55 | Demo inventario, venta y recepción SIMULADAS | Saldos y trazabilidad comprobados |
| 55–65 | IoT e historial, si hay permiso | Lectura o simulación identificada y límites por documentar |
| 65–75 | Preguntas a Saiki y análisis de demanda | Contraste de respuestas, sin prometer precisión |
| 75–85 | Conciliación final, entrevista y usabilidad | Diferencias y comentarios del dueño |
| 85–90 | Acuerdos, devolución/custodia de datos | Responsable, fecha y siguiente revisión |

Versión de 60 minutos: reduce catálogo a 10 productos, prepara la demo de antemano,
combina entrevista con recorrido y deja sensores/pronósticos para una segunda sesión
si no hay permisos, datos o dispositivos. No omitas permisos ni conciliación.

## Criterios de éxito y seguimiento

- 10–20 productos identificados sin confundir presentaciones; 100 % de unidades y
  ubicaciones de la muestra acordadas con el encargado.
- Saldo de cada producto coincide con conteo/documentos; cualquier diferencia queda explicada.
- Venta y recepción de muestra tienen responsable, cantidad, fecha y saldo trazables.
- Ningún registro de otra empresa visible ni datos reales modificados por la demo.
- Un enlace activa la cuenta, login y logout funcionan y no se comparten secretos.
- Si hay IoT: unidad y límite documentados, historial verificable, sin lecturas inventadas.
- Toda respuesta usada de Saiki coincide con la fuente o reconoce que no tiene datos.
- Pronósticos identifican procedencia y limitaciones; se acuerda evaluación posterior
  con ventas reales y comparación temporal, no una promesa de “precisión” en la visita.
- Dueño y encargado pueden describir cómo les ayudaría en sus **tres** problemas.

Antes de un piloto operativo prolongado deben resolverse los fallos altos del
informe y repetirse las pruebas. Durante las primeras semanas registra diferencias,
tiempos de conteo, quiebres observados y alertas atendidas; compara contra la línea
base de la misma tienda. No atribuyas una mejora a PsiTwin sin evidencia comparable.
