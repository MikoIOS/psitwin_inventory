> Actualizacion: el bloqueo de inventario vacio fue corregido y probado. Consulta [Correccion del inventario](CORRECCION_INVENTARIO_FRONTEND.md). El resto del informe conserva los resultados historicos y los demas hallazgos pendientes.

# Informe de pruebas integrales de PsiTwin Inventory

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


Resumen de 101 comprobaciones: {'Aprobado': 98, 'No probado': 2, 'Fallido': 1}. Las 46 preguntas se valoran aparte, por contenido, no solo HTTP.

| ID | Módulo/acción | Datos | Esperado | Obtenido | Estado | Evidencia / error |
|---|---|---|---|---|---|---|
| P001 | POST /auth/register | SIMULADOS | [201] | HTTP 201; 248.43 ms | Aprobado | pruebas.json #P001; — |
| P002 | POST /auth/login | SIMULADOS | [403] | HTTP 403; 105.78 ms | Aprobado | pruebas.json #P002; — |
| P003 | POST /auth/verification/confirm | SIMULADOS | [200] | HTTP 200; 26.04 ms | Aprobado | pruebas.json #P003; — |
| P004 | POST /auth/login | SIMULADOS | [200] | HTTP 200; 117.0 ms | Aprobado | pruebas.json #P004; — |
| P005 | Bienvenida personalizada capturada | SIMULADOS | 2 mensajes: verificación + bienvenida | 2 | Aprobado | pruebas.json #P005; — |
| P006 | GET /auth/me | SIMULADOS | [200] | HTTP 200; 6.17 ms | Aprobado | pruebas.json #P006; — |
| P007 | POST /almacenes | SIMULADOS | [201] | HTTP 201; 123.96 ms | Aprobado | pruebas.json #P007; — |
| P008 | POST /zonas | SIMULADOS | [201] | HTTP 201; 33.09 ms | Aprobado | pruebas.json #P008; — |
| P009 | POST /racks | SIMULADOS | [201] | HTTP 201; 45.56 ms | Aprobado | pruebas.json #P009; — |
| P010 | POST /racks | SIMULADOS | [201] | HTTP 201; 22.83 ms | Aprobado | pruebas.json #P010; — |
| P011 | POST /zonas | SIMULADOS | [201] | HTTP 201; 9.79 ms | Aprobado | pruebas.json #P011; — |
| P012 | POST /racks | SIMULADOS | [201] | HTTP 201; 16.87 ms | Aprobado | pruebas.json #P012; — |
| P013 | POST /zonas | SIMULADOS | [201] | HTTP 201; 10.28 ms | Aprobado | pruebas.json #P013; — |
| P014 | POST /racks | SIMULADOS | [201] | HTTP 201; 22.4 ms | Aprobado | pruebas.json #P014; — |
| P015 | PUT /almacenes/cb8cc600-ef2e-49f9-98d4-28de1c430f5d | SIMULADOS | [200] | HTTP 200; 16.36 ms | Aprobado | pruebas.json #P015; — |
| P016 | POST /proveedores | SIMULADOS | [201] | HTTP 201; 298.78 ms | Aprobado | pruebas.json #P016; — |
| P017 | POST /operarios | SIMULADOS | [201] | HTTP 201; 185.34 ms | Aprobado | pruebas.json #P017; — |
| P018 | POST /auth/login | SIMULADOS | [200] | HTTP 200; 122.91 ms | Aprobado | pruebas.json #P018; — |
| P019 | PATCH /auth/me/password | SIMULADOS | [200] | HTTP 200; 267.5 ms | Aprobado | pruebas.json #P019; — |
| P020 | POST /auth/login | SIMULADOS | [200] | HTTP 200; 139.97 ms | Aprobado | pruebas.json #P020; — |
| P021 | POST /auth/login | SIMULADOS | [200] | HTTP 200; 146.36 ms | Aprobado | pruebas.json #P021; — |
| P022 | PATCH /auth/me/password | SIMULADOS | [200] | HTTP 200; 244.67 ms | Aprobado | pruebas.json #P022; — |
| P023 | POST /auth/login | SIMULADOS | [200] | HTTP 200; 100.51 ms | Aprobado | pruebas.json #P023; — |
| P024 | POST /inventarios | SIMULADOS | [200] | HTTP 200; 15.43 ms | Aprobado | pruebas.json #P024; — |
| P025 | POST /productos | SIMULADOS | [201] | HTTP 201; 29.32 ms | Aprobado | pruebas.json #P025; — |
| P026 | PUT /productos/64ade511-6258-4c38-a7b7-d6f328de157a | SIMULADOS | [200] | HTTP 200; 18.37 ms | Aprobado | pruebas.json #P026; — |
| P027 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 232.84 ms | Aprobado | pruebas.json #P027; — |
| P028 | POST /productos | SIMULADOS | [201] | HTTP 201; 10.73 ms | Aprobado | pruebas.json #P028; — |
| P029 | PUT /productos/ac5a34ca-ebcd-46d9-9018-5d3318f27a50 | SIMULADOS | [200] | HTTP 200; 20.13 ms | Aprobado | pruebas.json #P029; — |
| P030 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 56.16 ms | Aprobado | pruebas.json #P030; — |
| P031 | POST /productos | SIMULADOS | [201] | HTTP 201; 9.2 ms | Aprobado | pruebas.json #P031; — |
| P032 | PUT /productos/5b9d340a-e775-40f3-9115-784726070d58 | SIMULADOS | [200] | HTTP 200; 19.27 ms | Aprobado | pruebas.json #P032; — |
| P033 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 63.13 ms | Aprobado | pruebas.json #P033; — |
| P034 | POST /productos | SIMULADOS | [201] | HTTP 201; 14.33 ms | Aprobado | pruebas.json #P034; — |
| P035 | PUT /productos/d0370608-f0c7-4dca-ac5f-1de099d23e92 | SIMULADOS | [200] | HTTP 200; 21.81 ms | Aprobado | pruebas.json #P035; — |
| P036 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 63.26 ms | Aprobado | pruebas.json #P036; — |
| P037 | POST /productos | SIMULADOS | [201] | HTTP 201; 69.52 ms | Aprobado | pruebas.json #P037; — |
| P038 | PUT /productos/27695f6c-e5cc-4b8b-b74a-27271481ae54 | SIMULADOS | [200] | HTTP 200; 32.37 ms | Aprobado | pruebas.json #P038; — |
| P039 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 66.42 ms | Aprobado | pruebas.json #P039; — |
| P040 | POST /productos | SIMULADOS | [201] | HTTP 201; 10.16 ms | Aprobado | pruebas.json #P040; — |
| P041 | PUT /productos/bc9f35fc-bcaa-4c6f-80aa-d9c653097f58 | SIMULADOS | [200] | HTTP 200; 21.11 ms | Aprobado | pruebas.json #P041; — |
| P042 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 54.46 ms | Aprobado | pruebas.json #P042; — |
| P043 | POST /productos | SIMULADOS | [201] | HTTP 201; 8.75 ms | Aprobado | pruebas.json #P043; — |
| P044 | PUT /productos/03802bd1-e977-4cd8-b6b9-bd86cb129a7e | SIMULADOS | [200] | HTTP 200; 16.98 ms | Aprobado | pruebas.json #P044; — |
| P045 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 49.98 ms | Aprobado | pruebas.json #P045; — |
| P046 | POST /productos | SIMULADOS | [201] | HTTP 201; 8.91 ms | Aprobado | pruebas.json #P046; — |
| P047 | PUT /productos/65c4407a-2b31-4ea1-987a-5f8984d8b109 | SIMULADOS | [200] | HTTP 200; 17.42 ms | Aprobado | pruebas.json #P047; — |
| P048 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 51.33 ms | Aprobado | pruebas.json #P048; — |
| P049 | POST /productos | SIMULADOS | [201] | HTTP 201; 9.35 ms | Aprobado | pruebas.json #P049; — |
| P050 | PUT /productos/396b2d60-23fb-4a9a-b9b0-ca538b103374 | SIMULADOS | [200] | HTTP 200; 17.69 ms | Aprobado | pruebas.json #P050; — |
| P051 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 56.89 ms | Aprobado | pruebas.json #P051; — |
| P052 | POST /productos | SIMULADOS | [201] | HTTP 201; 10.36 ms | Aprobado | pruebas.json #P052; — |
| P053 | PUT /productos/f7a30734-a970-453d-b5d9-fc44bbc33bb9 | SIMULADOS | [200] | HTTP 200; 20.49 ms | Aprobado | pruebas.json #P053; — |
| P054 | POST /detalles-inventario | SIMULADOS | [201] | HTTP 201; 65.47 ms | Aprobado | pruebas.json #P054; — |
| P055 | Persistencia de SKU/precios/unidad solicitados | SIMULADOS | Campos no disponibles en DTO actual | {"sku": null, "precio_compra": null, "precio_venta": null, "unidad_medida": null} | No probado | pruebas.json #P055; No disponible en modelo/API |
| P056 | Relaciones persistidas | SIMULADOS | 4 racks / 10 productos | {"racks": 4, "productos": 10} | Aprobado | pruebas.json #P056; — |
| P057 | POST /ordenes-reposicion | SIMULADOS | [201] | HTTP 201; 61.13 ms | Aprobado | pruebas.json #P057; — |
| P058 | PATCH /ordenes-reposicion/4aef8085-df33-4c7a-9da4-f4eaa2eafb13/validar | SIMULADOS | [200] | HTTP 200; 45.84 ms | Aprobado | pruebas.json #P058; — |
| P059 | POST /recepciones | SIMULADOS | [201] | HTTP 201; 242.52 ms | Aprobado | pruebas.json #P059; — |
| P060 | Entrada arroz 30+20=50 | SIMULADOS | 50 | 50 | Aprobado | pruebas.json #P060; — |
| P061 | POST /recepciones | SIMULADOS | [400, 409] | HTTP 409; 11.43 ms | Aprobado | pruebas.json #P061; — |
| P062 | POST /movimientos | SIMULADOS | [201] | HTTP 201; 70.01 ms | Aprobado | pruebas.json #P062; — |
| P063 | Venta arroz 50-8=42 | SIMULADOS | 42 | 42 | Aprobado | pruebas.json #P063; — |
| P064 | POST /movimientos | SIMULADOS | [404, 409, 422] | HTTP 409; 65.2 ms | Aprobado | pruebas.json #P064; — |
| P065 | POST /movimientos | SIMULADOS | [404, 409, 422] | HTTP 422; 9.22 ms | Aprobado | pruebas.json #P065; — |
| P066 | POST /movimientos | SIMULADOS | [404, 409, 422] | HTTP 422; 6.23 ms | Aprobado | pruebas.json #P066; — |
| P067 | POST /movimientos | SIMULADOS | [404, 409, 422] | HTTP 404; 12.59 ms | Aprobado | pruebas.json #P067; — |
| P068 | POST /movimientos | SIMULADOS | [422] | HTTP 422; 4.73 ms | Aprobado | pruebas.json #P068; — |
| P069 | POST /movimientos | SIMULADOS | [201] | HTTP 201; 53.23 ms | Aprobado | pruebas.json #P069; — |
| P070 | POST /movimientos | SIMULADOS | [422] | HTTP 422; 5.21 ms | Aprobado | pruebas.json #P070; — |
| P071 | POST /movimientos | SIMULADOS | [422] | HTTP 422; 5.29 ms | Aprobado | pruebas.json #P071; — |
| P072 | POST /movimientos | SIMULADOS | [201] | HTTP 201; 58.11 ms | Aprobado | pruebas.json #P072; — |
| P073 | POST /movimientos | SIMULADOS | [201, 409] | HTTP 201; 60.93 ms | Aprobado | pruebas.json #P073; — |
| P074 | Repetición de venta no descuenta dos veces | SIMULADOS | 17 si es idempotente; 16 indica repetición aplicada | 16 | Fallido | pruebas.json #P074; Repetición aplicada dos veces |
| P075 | Dos salidas simultáneas no generan stock negativo | SIMULADOS | 201+409; stock=1 | {"http": [409, 201], "stock": 1} | Aprobado | pruebas.json #P075; — |
| P076 | POST /detalles-inventario | SIMULADOS | [404] | HTTP 404; 13.1 ms | Aprobado | pruebas.json #P076; — |
| P077 | Transferencias | SIMULADOS | No fingir soporte | No hay endpoint de transferencia ni motivo TRANSFERENCIA | No probado | pruebas.json #P077; No disponible en modelo/API |
| P078 | GET /productos/64ade511-6258-4c38-a7b7-d6f328de157a | SIMULADOS | [404] | HTTP 404; 4.53 ms | Aprobado | pruebas.json #P078; — |
| P079 | GET /inventarios/7587bfea-bdf9-45ec-9677-e5cd1cacd98d | SIMULADOS | [404] | HTTP 404; 8.44 ms | Aprobado | pruebas.json #P079; — |
| P080 | GET /racks/15a92e81-dd65-482e-9d53-b45a9a3e753f | SIMULADOS | [404] | HTTP 404; 8.64 ms | Aprobado | pruebas.json #P080; — |
| P081 | POST /dispositivos | SIMULADOS | [201] | HTTP 201; 48.83 ms | Aprobado | pruebas.json #P081; — |
| P082 | Ingesta sensor normal | SIMULADOS | true | true | Aprobado | pruebas.json #P082; — |
| P083 | Ingesta sensor alta | SIMULADOS | true | true | Aprobado | pruebas.json #P083; — |
| P084 | Ingesta sensor alta repetida | SIMULADOS | true | true | Aprobado | pruebas.json #P084; — |
| P085 | Ingesta sensor baja | SIMULADOS | true | true | Aprobado | pruebas.json #P085; — |
| P086 | Ingesta sensor recuperada | SIMULADOS | true | true | Aprobado | pruebas.json #P086; — |
| P087 | Ingesta sensor antigua | SIMULADOS | true | true | Aprobado | pruebas.json #P087; — |
| P088 | Ingesta sensor conexión recuperada | SIMULADOS | true | true | Aprobado | pruebas.json #P088; — |
| P089 | IoT persistido sin interpolación | SIMULADOS | 7 | 7 | Aprobado | pruebas.json #P089; — |
| P090 | Eventos proactivos producidos | SIMULADOS | Eventos reales del backend ante lecturas SIMULADAS; no prueba audio físico | 7 | Aprobado | pruebas.json #P090; — |
| P091 | GET /dispositivos/18880727-a15c-418f-8c3d-139e34105c4b/lecturas | SIMULADOS | [200] | HTTP 200; 16.67 ms | Aprobado | pruebas.json #P091; — |
| P092 | GET /dispositivos/18880727-a15c-418f-8c3d-139e34105c4b/lecturas | SIMULADOS | [200] | HTTP 200; 16.0 ms | Aprobado | pruebas.json #P092; — |
| P093 | GET /dispositivos/18880727-a15c-418f-8c3d-139e34105c4b/lecturas | SIMULADOS | [200] | HTTP 200; 14.89 ms | Aprobado | pruebas.json #P093; — |
| P094 | GET /dispositivos | SIMULADOS | [200] | HTTP 200; 14.89 ms | Aprobado | pruebas.json #P094; — |
| P095 | GET /dispositivos | SIMULADOS | [200] | HTTP 200; 6.68 ms | Aprobado | pruebas.json #P095; — |
| P096 | GET /alertas | SIMULADOS | [200] | HTTP 200; 9.56 ms | Aprobado | pruebas.json #P096; — |
| P097 | GET /inventarios/7587bfea-bdf9-45ec-9677-e5cd1cacd98d/historial | SIMULADOS | [200] | HTTP 200; 17.05 ms | Aprobado | pruebas.json #P097; — |
| P098 | GET /forecast/almacenes/cb8cc600-ef2e-49f9-98d4-28de1c430f5d/productos/64ade511-6258-4c38-a7b7-d6f328de157a | SIMULADOS | [200] | HTTP 200; 25.18 ms | Aprobado | pruebas.json #P098; — |
| P099 | GET /analisis/modelo | SIMULADOS | [200] | HTTP 200; 72.3 ms | Aprobado | pruebas.json #P099; — |
| P100 | GET /analisis/historico | SIMULADOS | [200] | HTTP 200; 14.49 ms | Aprobado | pruebas.json #P100; — |
| P101 | GET /saiki/health | SIMULADOS | [200] | HTTP 200; 2275.89 ms | Aprobado | pruebas.json #P101; — |

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

| S01 | ¿Cuántos productos tengo registrados? | Tienes 10 productos registrados en tu catálogo. | MongoDB: 10 productos | Correcta | No demostrado; dato verificado | 19.35 |
| S02 | ¿Qué productos están por agotarse? | Sin respuesta utilizable: JSONDecodeError | Azúcar=1, Aceite=0; mínimo=5 por ubicación | Fallida | No evaluable: sin respuesta | 124.12 |
| S03 | ¿Cuántas unidades de arroz tengo? | Sin respuesta utilizable: TimeoutError | Arroz=41 al cierre; 42 antes de salida por vencimiento | Fallida | No evaluable: sin respuesta | 55007.29 |
| S04 | ¿En qué rack está almacenada la leche? | Sin respuesta utilizable: TimeoutError | Leche en C-01 | Fallida | No evaluable: sin respuesta | 55015.82 |
| S05 | ¿Qué productos están agotados? | Sin respuesta utilizable: JSONDecodeError | Aceite=0 | Fallida | No evaluable: sin respuesta | 499.35 |
| S06 | ¿Cuál es el stock total del arroz? | Sin respuesta utilizable: TimeoutError | Arroz=41 | Fallida | No evaluable: sin respuesta | 1384698.65 |
| S07 | ¿Qué productos necesitan reposición? | Sin respuesta utilizable: TimeoutError | Faltantes observables, sin pronóstico de compra válido | Fallida | No evaluable: sin respuesta | 163480.97 |
| S08 | ¿Cuáles son los productos con mayor stock? | Sin respuesta utilizable: TimeoutError | Gaseosa=70, Arroz=41, Agua=25 | Fallida | No evaluable: sin respuesta | 55028.08 |
| S09 | ¿Cuántas unidades de arroz vendí hoy? | Sin respuesta utilizable: TimeoutError | Venta de arroz=8; vencimiento=1 separado | Fallida | No evaluable: sin respuesta | 54997.52 |
| S10 | ¿Qué productos tuvieron más salidas esta semana? | Sin respuesta utilizable: TimeoutError | Ventas de arroz=8, azúcar=3, galletas=2 | Fallida | No evaluable: sin respuesta | 55019.29 |
| S11 | ¿Cuántas entradas de mercadería se registraron? | Encontré 1 entrada entre los movimientos recientes consultados. | Una entrada de 20 | Correcta | No demostrado; dato verificado | 51.83 |
| S12 | ¿Cuál fue el último movimiento de inventario? | Encontré 6 movimientos recientes. Los detalles están disponibles en la respuesta. | Última venta: azúcar, 3 unidades | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 18.64 |
| S13 | ¿Qué productos tuvieron ajustes? | Tienes 10 productos registrados en tu catálogo. | No hay AJUSTE; API lo rechaza | Fallida | Confunde intención o alcance; revisar texto | 10.47 |
| S14 | ¿Cuántas unidades ingresaron al almacén? | Sin respuesta utilizable: TimeoutError | Entrada=20 | Fallida | No evaluable: sin respuesta | 55021.83 |
| S15 | ¿Qué movimientos se realizaron ayer? | Encontré 6 movimientos recientes. Los detalles están disponibles en la respuesta. | No hay movimientos de ayer; los 6 son del día de ejecución | Fallida | Confunde intención o alcance; revisar texto | 32.54 |
| S16 | ¿Cuántos racks tengo? | Tienes 1 almacenes, 3 zonas y 4 racks. Almacenes: Almacén principal SIMULADO revisado. | 4 racks | Correcta | No demostrado; dato verificado | 23.84 |
| S17 | ¿Qué productos están en el Rack A-01? | Yogur: 8 unidades en almacén Almacén principal SIMULADO revisado, zona Refrigerados SIMULADO, rack C-01; Gaseosa: 70 unidades en almacén Almacén principal SIMULADO revisado, zona Bebidas SIMULADO, rack A-01; Conserva: 9 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01; Leche: 12 unidades en almacén Almacén principal SIMULADO revisado, zona Refrigerados SIMULADO, rack C-01; Arroz: 41 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01; Galletas: 16 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01; Azúcar: 1 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01; Agua: 25 unidades en almacén Almacén principal SIMULADO revisado, zona Bebidas SIMULADO, rack A-02; Aceite: 0 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01; Fideos: 14 unidades en almacén Almacén principal SIMULADO revisado, zona Alimentos SIMULADO, rack B-01. | A-01: Gaseosa=70; no otros productos | Fallida | Confunde intención o alcance; revisar texto | 38.0 |
| S18 | ¿Qué racks pertenecen a la zona de bebidas? | ¿Quieres consultar tus datos, aprender a usar una sección de PsiTwin o conversar sobre otro tema? Cuéntame un poco más. | Bebidas: A-01 y A-02 | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 8.74 |
| S19 | ¿Dónde se encuentra el arroz? | Arroz está en el rack B-01. | Arroz en B-01 | Correcta | No demostrado; dato verificado | 45.85 |
| S20 | ¿Qué racks tienen sensores instalados? | Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Solo C-01 tiene sensor | Correcta | No demostrado; dato verificado | 85.66 |
| S21 | ¿Cuál es la temperatura actual del Rack C-01? | Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Último valor registrado: 4.0 °C, fecha 2026-10-27 21:25:17.978945+00:00.<br><br>La lectura no es reciente; no permite afirmar un estado actual normal.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Último valor=4 °C, lectura desactualizada al preguntar | Correcta | No demostrado; dato verificado | 30.24 |
| S22 | ¿Qué sensores tiene el Rack A-01? | No encontré sensores de ese rack en tu empresa. Revisa el código o selecciona un dispositivo en Monitoreo. | A-01 sin sensores | Correcta | No demostrado; dato verificado | 38.08 |
| S23 | ¿Hay temperaturas fuera de rango? | Hay 0 alertas de sensores activas. Se muestran hasta 50 incidentes.<br><br>Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Último valor registrado: 4.0 °C, fecha 2026-10-27 21:25:17.978945+00:00.<br><br>La lectura no es reciente; no permite afirmar un estado actual normal.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Sin incidentes activos al cierre; no prueba seguridad actual | Correcta | No demostrado; dato verificado | 51.79 |
| S24 | ¿Cuál fue la temperatura máxima de ayer? | Periodo: 2026-10-26T00:00:00-05:00 a 2026-10-27T00:00:00-05:00 (Lima).<br><br>Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>No hay mediciones históricas disponibles en el periodo; no puedo calcular extremos ni tendencias.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Sin lecturas de ayer | Correcta | No demostrado; dato verificado | 40.54 |
| S25 | ¿Qué sensores están desconectados? | Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Un dispositivo con lectura antigua; no hardware físico | Correcta | No demostrado; dato verificado | 22.3 |
| S26 | ¿Cómo cambió la humedad durante el día? | Periodo: 2026-10-26T16:56:41.030968-05:00 a 2026-10-27T16:56:41.030968-05:00 (Lima).<br><br>Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Humedad: mínimo 20.0, máximo 80.0, promedio 55.00 %; 6 mediciones. Estadísticas de minutos del periodo completo.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | Humedad 6 valores: mínimo20, máximo80, promedio55 % | Correcta | No demostrado; dato verificado | 64.98 |
| S27 | ¿Se detectó movimiento en el almacén? | Encontré 6 movimientos recientes. Los detalles están disponibles en la respuesta. | No hay sensor PIR; no confundir con 6 movimientos de stock | Fallida | Confunde intención o alcance; revisar texto | 30.3 |
| S28 | ¿Qué alertas de sensores están activas? | Sin datos disponibles. No hay lecturas actuales de sensores conectados.<br><br>Sensor T/H SIMULADO — Almacén principal SIMULADO revisado / Refrigerados SIMULADO / C-01: Sin datos disponibles<br><br>Lectura desactualizada o sin fecha válida; no confirma el estado actual de la medición.<br><br>No hay alertas abiertas registradas en los equipos visibles. Esto no confirma que todos los equipos funcionen correctamente.<br><br>Historial disponible: 3 incidentes registrados; se muestran los 20 más recientes. No se infiere frecuencia sin un periodo de observación completo.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: actualidad = 7200.038432 s (límite 5.0 s), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.970000; parámetro actualidad; valor 7200.038432; límite 5.0.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: hum = 80.0 % (límite 65.0 %), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.939000; parámetro hum; valor 80.0; límite 65.0.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: t_int = 9.0 °C (límite 6.0 °C), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.937000; parámetro t_int; valor 9.0; límite 6.0. | Tres incidentes históricos resueltos; ninguno activo | Correcta | No demostrado; dato verificado | 42.17 |
| S29 | ¿Cuánto arroz podría vender la próxima semana? | ¿Quieres consultar tus datos, aprender a usar una sección de PsiTwin o conversar sobre otro tema? Cuéntame un poco más. | Producto nuevo sin historia suficiente; no forecast válido | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 8.98 |
| S30 | ¿Qué productos necesitaré reponer pronto? | ¿Para qué producto y almacén deseas consultar la demanda? | Sin compra predictiva calculable con estos datos | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 62.55 |
| S31 | ¿Cuál es la demanda estimada de leche? | No hay registros históricos importados para estos filtros. | Leche sin historial | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 46.63 |
| S32 | ¿Qué producto podría agotarse primero? | Sin respuesta utilizable: JSONDecodeError | No inferible sin pronóstico válido | Fallida | No evaluable: sin respuesta | 365.02 |
| S33 | ¿Cuántas unidades debería comprar? | Sin respuesta utilizable: TimeoutError | No hay recomendación cuantitativa válida | Fallida | No evaluable: sin respuesta | 55011.1 |
| S34 | ¿Qué productos presentan mayor demanda? | No hay registros históricos importados para estos filtros. | No hay historial importado | Correcta | No demostrado; dato verificado | 30.6 |
| S35 | ¿Cómo registro un producto? | Tienes 10 productos registrados en tu catálogo. | Proveedor → Productos → Nuevo producto | Fallida | Confunde intención o alcance; revisar texto | 11.37 |
| S36 | ¿Cómo creo un rack? | ¿Quieres consultar tus datos, aprender a usar una sección de PsiTwin o conversar sobre otro tema? Cuéntame un poco más. | Empresa → almacén → zona → Nuevo rack | Fallida | Confunde intención o alcance; revisar texto | 8.12 |
| S37 | ¿Cómo agrego un sensor? | Sin datos disponibles. No hay lecturas actuales de sensores conectados.<br><br>Sensor T/H SIMULADO — Almacén principal SIMULADO revisado / Refrigerados SIMULADO / C-01: Sin datos disponibles<br><br>Lectura desactualizada o sin fecha válida; no confirma el estado actual de la medición.<br><br>No hay alertas abiertas registradas en los equipos visibles. Esto no confirma que todos los equipos funcionen correctamente.<br><br>Historial disponible: 3 incidentes registrados; se muestran los 20 más recientes. No se infiere frecuencia sin un periodo de observación completo.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: actualidad = 7200.038432 s (límite 5.0 s), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.970000; parámetro actualidad; valor 7200.038432; límite 5.0.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: hum = 80.0 % (límite 65.0 %), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.939000; parámetro hum; valor 80.0; límite 65.0.<br><br>Sensor T/H SIMULADO: RESUELTA — Sensor T/H SIMULADO · Rack C-01: t_int = 9.0 °C (límite 6.0 °C), desde 2026-10-27T21:25:17+00:00; fecha 2026-10-27 21:25:17.937000; parámetro t_int; valor 9.0; límite 6.0. | Empresa → Monitoreo → Nuevo dispositivo | Fallida | Confunde intención o alcance; revisar texto | 34.57 |
| S38 | ¿Cómo registro una venta? | Encontré 6 movimientos recientes. Los detalles están disponibles en la respuesta. | Operario → Movimientos → SALIDA/VENTA | Fallida | Confunde intención o alcance; revisar texto | 22.83 |
| S39 | ¿Cómo consulto los movimientos? | Encontré 6 movimientos recientes. Los detalles están disponibles en la respuesta. | Página Movimientos con filtros | Fallida | Confunde intención o alcance; revisar texto | 21.51 |
| S40 | ¿Cómo veo las alertas? | No tienes alertas activas. | Alertas visibles en inventario/monitoreo según módulo | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 28.76 |
| S41 | ¿Cómo interpreto los pronósticos? | ¿Para qué producto y almacén deseas consultar la demanda? | Análisis, historial, horizonte y límites; sin garantía de precisión | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 47.58 |
| S42 | ¿Cuántos operarios tengo? | Tienes 1 operarios registrados: 1 activos y 0 inactivos. | 1 operario activo | Correcta | No demostrado; dato verificado | 9.66 |
| S43 | ¿Qué productos tengo en un almacén inexistente? | Tienes 1 almacenes, 3 zonas y 4 racks. Almacenes: Almacén principal SIMULADO revisado. | Almacén inexistente debe rechazarse o aclararse | Fallida | Confunde intención o alcance; revisar texto | 15.45 |
| S44 | ¿Cuál fue la temperatura de un sensor sin lecturas? | Sensor T/H SIMULADO (18880727-a15c-418f-8c3d-139e34105c4b) · Rack C-01 · desconectado. Tipos: Temperatura interna, Humedad.<br><br>Último valor registrado: 4.0 °C, fecha 2026-10-27 21:25:17.978945+00:00.<br><br>La lectura no es reciente; no permite afirmar un estado actual normal.<br><br>Las lecturas y alertas no prueban por sí solas daño en un producto ni una causa técnica. | No seleccionar otro sensor para responder por uno sin lecturas | Fallida | Confunde intención o alcance; revisar texto | 33.53 |
| S45 | ¿Cuánto vendí en un período sin registros? | ¿Quieres consultar tus datos, aprender a usar una sección de PsiTwin o conversar sobre otro tema? Cuéntame un poco más. | Solicitar fechas concretas si el periodo no está definido | Incompleta / aclaración insuficiente | Confunde intención o alcance; revisar texto | 6.49 |
| S46 | Hola, ¿qué puedes hacer por mi tienda? | ¡Hola! 👋 Soy Saiki Ψ, tu asistente inteligente de PsiTwin. Estoy aquí para ayudarte a gestionar tu inventario, conocer el estado de tus almacenes, interpretar predicciones de demanda y resolver dudas sobre cómo utilizar la plataforma. ¿Qué puedo hacer por ti hoy? | Identidad y capacidades sin inventar datos | Correcta | No demostrado; dato verificado | 7.96 |

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

| ¿Qué productos están agotados? | AttributeError | — | 1140.42 |
| ¿Qué productos están por agotarse? | AttributeError | — | 190.12 |
| ¿Cómo registro un producto? | Los productos se crean desde la cuenta de PROVEEDOR: abre Productos, pulsa Nuevo producto, completa el formulario y guarda. La empresa y los operarios consultan el catálogo, pero no tienen el botón para crear productos. Si eres la empresa, registra o contacta al proveedor desde Proveedores; él debe ingresar con sus credenciales y registrar sus productos. Registrar un producto no añade stock automáticamente: las existencias se gestionan en Inventario y Recepciones. | 200 | 19.42 |
| ¿Cómo creo un rack? | Abre Inicio, un almacén y su zona; pulsa Nuevo rack. Indica código, nivel, carga máxima y temperaturas cuando correspondan, y guarda. La carga máxima no se modifica después de crear el rack. Solo los racks Libres reciben mercadería; revisa el estado en la ficha del rack. | 200 | 9.89 |
| ¿Cómo agrego un sensor? | En Sensores → Monitoreo, selecciona almacén, zona y rack en Monitoreo por rack. El selector muestra los tipos comunicados por los dispositivos; un rack sin dispositivos dice Sin sensores. Pulsa el tipo y, si hay varios dispositivos, elige uno. Revisa conexión, fecha de lectura, medición y umbrales. El Historial permite última hora, 24 horas, 7 días, 30 días o un rango personalizado, con gráfico y tabla paginados. Los datos ausentes no indican normalidad. Las tarjetas inferiores conservan acceso al detalle, edición, token y alertas del dispositivo. Una alerta no confirma daño físico. | 200 | 8.73 |
| ¿Cómo registro una venta? | Para registrar una empresa, completa sus datos, el nombre del CEO, RUC, sector, telefono, Gmail y ambas contrasenas de PsiTwin. Pulsa Registrar empresa y abre el enlace de verificacion que llega a tu correo para activar la cuenta. Despues inicia sesion con Gmail y contrasena de PsiTwin. No necesitas Google OAuth. En Perfil puedes editar los datos y cambiar tu contrasena. | 200 | 7.03 |
| ¿Cómo consulto los movimientos? | En Movimientos consulta el historial con filtros de tipo, motivo, operario y producto. Usa Registrar salida si tu rol lo permite y completa la ubicación, cantidad y motivo. Las entradas de mercadería proceden del flujo de Recepciones. El stock debe corresponder a movimientos y ubicaciones reales. | 200 | 9.85 |
| ¿Cómo veo las alertas? | En Sensores → Monitoreo, selecciona almacén, zona y rack en Monitoreo por rack. El selector muestra los tipos comunicados por los dispositivos; un rack sin dispositivos dice Sin sensores. Pulsa el tipo y, si hay varios dispositivos, elige uno. Revisa conexión, fecha de lectura, medición y umbrales. El Historial permite última hora, 24 horas, 7 días, 30 días o un rango personalizado, con gráfico y tabla paginados. Los datos ausentes no indican normalidad. Las tarjetas inferiores conservan acceso al detalle, edición, token y alertas del dispositivo. Una alerta no confirma daño físico. | 200 | 6.7 |
| ¿Cómo interpreto los pronósticos? | Como empresa abre Análisis, selecciona almacén y producto, cambia a la vista de predicción y elige 1, 7, 30 o 90 días en Días a pronosticar. AutoGluon calcula la demanda cuando hay un modelo e historial válidos. La demanda prevista no es el stock real. Si faltan datos o el modelo no está disponible, la plataforma debe indicarlo; no se inventan pronósticos. | 200 | 7.85 |
| ¿Cuántos productos tengo registrados? | Tienes 10 productos registrados en tu catálogo. | 200 | 15.94 |

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
