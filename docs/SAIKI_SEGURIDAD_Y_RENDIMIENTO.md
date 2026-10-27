# Corrección de Saiki: validación y cambios pendientes

## Cambios implementados

- El ámbito de inventarios visibles es local a cada ejecución. Ningún atributo
  del registro de herramientas conserva permisos de una solicitud.
- Los esquemas de herramientas se pasan explícitamente al loop y a Ollama.
  El loop también rechaza herramientas fuera de la selección de esa consulta.
- Solo el estado general utiliza la respuesta directa de inventario.
  Movimientos, alertas, productos, ubicaciones, stock y riesgos tienen rutas
  de intención específicas; lo ambiguo se deja al modelo.
- Las predicciones disponibles son de siete días de demanda. `dias` conserva
  su significado de ventana histórica. `horizonte_dias` solo admite 7.
- La respuesta sin almacenes no hace afirmaciones sobre el catálogo.
- Se conservan answer, data, visualization, sources, warnings y context.
- El historial admite solo mensajes textuales de usuario/asistente; no roles
  de sistema ni instrucciones de herramientas.

## JWT: corrección no aplicada

Settings lee SECRET_KEY y ALGORITHM. El archivo local contiene los nombres
JWT_SECRET_KEY y JWT_ALGORITHM, que se ignoran por falta de aliases y por
extra="ignore". No se modificó Settings, .env ni ninguna clave en esta etapa.

La propuesta es aceptar ambos nombres con AliasChoices, dando prioridad a
SECRET_KEY y ALGORITHM para preservar despliegues ya configurados. Antes de
aplicarla se debe comprobar la configuración efectiva del proceso servidor.
Si únicamente existe JWT_SECRET_KEY, el alias activaría una clave diferente
de la predeterminada usada antes: los tokens anteriores podrían dejar de
verificarse y requerir nuevo inicio de sesión. También debe comprobarse el
algoritmo antes de aceptar el alias correspondiente. Este cambio requiere
autorización expresa; no se recomienda una transición que acepte la clave
predeterminada insegura.

## Instrumentación y reproducción

Las rutas /api/v1/saiki/ask y /chat devuelven X-Saiki-Request-ID y
X-Saiki-Revision. La revisión es una huella de los archivos Saiki calculada
al construir el servicio, para identificar el código cargado por el proceso.
No es un número de versión de Git ni prueba de la versión de las dependencias.

Con logging INFO habilitado se registran endpoint y revisión, intención,
presencia de IDs, tamaño del historial, tiempo de servicio, autorización,
consultas de herramientas, inferencias y métricas de tokens/carga de Ollama.
No se registra texto del usuario, valores de contexto, tokens ni contraseñas.
El tiempo de ruta incluye validación, dependencias y serialización de respuesta;
no incluye transporte de red hasta el cliente. El tiempo de consulta de
herramienta puede incluir procesamiento de servicio; no es exclusivamente
tiempo de ejecución del servidor MongoDB.

Para reproducir el caso, con el servidor autorizado ya levantado y un JWT
válido, enviar a /api/v1/saiki/ask:

```json
{"message":"Hola Saiki, ¿cómo está mi inventario?"}
```

Repetir también en /chat y comparar la revisión, intención general, origen
backend, una herramienta y cero inferencias. Medir separadamente modelo frío,
caliente, solicitudes específicas y concurrencia; conservar p50/p95.
No iniciar la aplicación contra datos reales solo para esta prueba: su
lifespan crea índices. No consultar el GET de riesgo con generación de alertas.

No se aumentaron timeouts ni cambiaron parámetros Ollama. No hay medición
real antes/después: los 120 segundos son el antecedente proporcionado, no un
benchmark reproducido. Tampoco se ha demostrado que MongoDB sea lento, por
lo que no se modificaron repositorios ni índices para optimizarlo.

## Pruebas y entorno

El Python 3.12 referenciado por los entornos existentes no pudo utilizarse.
El Python 3.11 de Inkscape está disponible, pero carece de pytest y de las
dependencias de la aplicación. Los binarios cp312 existentes no son compatibles.
No se creó ni reparó un entorno, ni se instalaron paquetes.

Se ejecutaron diez pruebas unittest en test_saiki_isolation_stdlib.py.
Compilan los métodos reales de los servicios desde su AST, sin importar
FastAPI/Pydantic/LightGBM. Cubren intercalación concurrente de dos empresas,
rechazo de inventario ajeno, selección local de herramientas, intenciones,
horizontes, cinco respuestas de estado, cero inferencias en resumen y errores.
Los colaboradores están simulados: no equivalen a integración JWT/MongoDB/
Ollama ni verifican el comportamiento efectivo de Pydantic.

Las pruebas adicionales de ForecastArgs y del predictor simulado están en
test_saiki_service.py; su ejecución completa sigue pendiente del entorno.
La suite pytest no pudo arrancar: No module named pytest.

Autorizaciones pendientes: aplicar aliases JWT con su impacto en sesiones;
crear un entorno de pruebas separado y resolver sus dependencias. No se
modificaron fórmulas de riesgo, pesos ML, colecciones ni datos reales.
