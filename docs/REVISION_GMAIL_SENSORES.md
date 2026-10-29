# Revisión funcional de PsiTwin — 27 de octubre de 2026

## Acceso solicitado

El login muestra solo **Correo Gmail**, **Contraseña** e **Ingresar**. La contraseña
es la de PsiTwin creada al registrarse, no la contraseña de la cuenta Google.
Se retiraron el botón de login con Google y el texto de acceso alternativo.
La validación de Gmail se aplica en frontend y backend, con dominio exacto:
`gmail.com.attacker.test`, subdominios y otros dominios son rechazados.

El registro continúa verificando la identidad con Google, crea la contraseña de
PsiTwin y ahora rechaza correos que no sean Gmail. No se sustituye la verificación
de Google por una comprobación de dominio: se mantienen firma, correo verificado,
audiencia, emisor, expiración, PKCE, estado, nonce y vinculación por `sub`.
Las cuentas y contraseñas existentes no se modificaron. La restricción Gmail también
afecta el login de operarios y proveedores; cuentas antiguas con otro dominio
necesitan actualizar su correo para poder utilizar este acceso.

## Revisión del sistema

Se inspeccionaron el formulario y contrato de autenticación, registro OIDC,
servicios de dispositivos, consultas históricas, repositorios, estado de monitoreo,
enrutamiento de Saiki y manejo de errores. Se ejecutaron todas las pruebas backend
y frontend disponibles. Esto constituye una revisión funcional con regresión
automatizada; no una certificación exhaustiva de seguridad ni una prueba con
sensores físicos.

Correcciones encontradas durante la revisión:

- «Últimos 7 días» y «última semana» ahora consultan siete días completos, sin
  confundirlos con 24 horas o con el inicio de la semana calendario.
- «Temperatura» considera temperatura ambiente cuando el dispositivo solo mide
  ese parámetro. Una petición explícita de temperatura interna sigue respetándolo.
- Las preguntas de temperatura y humedad usan la consulta con selección de
  parámetro y comprobación de actualidad de la lectura.
- Fechas de lectura textuales inválidas se tratan como fecha desconocida.
- El informe general diferencia conexión de lectura reciente: una lectura antigua
  o sin fecha válida no se presenta como una medición actual confirmada.
- Un fallo de MongoDB al consultar sensores informa que no se pudieron consultar
  sensores y lecturas; no responde sobre inventario ni afirma que hay cero datos.

## Preguntas comprobadas

Estas conversaciones pasaron por el enrutador y servicio reales de Saiki,
repositorios y MongoDB temporal. El estado MQTT se controló durante las pruebas;
las mediciones eran datos de prueba explícitos, eliminados con la base temporal.
Se impidió llamar al LLM para verificar que las respuestas operativas procedieran
del backend y no de resultados inventados por el modelo.

| Pregunta | Qué se comprobó |
|---|---|
| ¿Qué sensores tiene el Rack A-01? | Tipos disponibles del rack |
| ¿Cuál es la temperatura actual del Rack A-01? | Valor y unidad de la lectura reciente |
| ¿Cuál es la temperatura del Rack A-02? | Sensor que solo mide temperatura ambiente |
| ¿Qué racks tienen sensores de humedad? | Inclusión de racks con ese parámetro |
| ¿Hay sensores desconectados? | Identificación del dispositivo desconectado |
| ¿Cuál fue la temperatura máxima de ayer en el Rack A-01? | Mínimo y máximo del día anterior, horario de Lima |
| ¿Cómo cambió la humedad en los últimos 7 días en el Rack A-01? | Ventana completa, resumen y exclusión de datos anteriores |
| ¿Cuántas alertas de sensores hubo este mes? | Conteo y conservación de incidentes resueltos |
| ¿Qué sensores estuvieron fuera de rango este mes? | Mensaje y rack del incidente |
| ¿Cuál es la humedad del Rack A-03? | Advertencia de lectura antigua |
| ¿Qué sensores tiene el Rack VACIO? | Ausencia de sensores sin inventar mediciones |

En todos los casos se comprobó que no aparecieran datos de otra empresa.
Se comprobaron adicionalmente errores de conexión y fechas ausentes.

## Resultados

- Backend completo: **349 pruebas aprobadas**, 3 omitidas y 26 subpruebas aprobadas.
- Frontend completo: **46 pruebas aprobadas** en 15 archivos.
- TypeScript y compilación Vite: aprobados. Persiste la advertencia previa del
  visualizador de audio de aproximadamente 646 kB.
- Sintaxis Python y comprobación de espacios Git: aprobadas.
- Evidencia backend: `artifacts/revision-gmail-sensores.xml`.

La suite cubre también sesión y perfil, bienvenida con SMTP controlado, inventario,
demanda, alertas y contratos de voz. Las omisiones son integraciones optativas de
AutoGluon, MongoDB adicional y Ollama. No se repitió la inferencia real de voz ni
la conversación con Qwen en esta revisión; las pruebas operativas de sensores
funcionan con datos del backend sin depender del modelo conversacional.
No se probaron dispositivos físicos, micrófono ni entrega real a Gmail.
El consentimiento real de Google sigue pendiente de configurar sus credenciales
privadas; el login Gmail con contraseña de una cuenta existente no realiza OAuth.

Reiniciar en Git Bash para cargar los cambios del backend:

```bash
./iniciar.cmd -Detener
./iniciar.cmd
```
