# Saiki: cantidades rápidas y verificables

Validación: 29 de octubre de 2026.

## Causa y cambio

Las rutas rápidas existentes cubrían resúmenes y listados generales, pero preguntas como «¿Cuánto stock tengo de Mango Kent?» o consultas con `id_producto` seleccionado podían pasar por la inferencia conversacional. También «Cantidad de Mango Kent» podía clasificarse como ambigua pese a ser una consulta de inventario.

Ahora las preguntas simples de cantidades se resuelven directamente contra el inventario autorizado, antes de preparar contexto para el modelo. Se conserva la IA existente para conversación y consultas que requieren otra interpretación. La lectura independiente del catálogo y los almacenes se realiza concurrentemente. No se añadió una caché de cantidades: cada consulta lee el stock actual.

El resultado identifica producto, cantidad, unidad y momento de consulta en `data.cantidades_verificadas`. No mezcla kg con unidades ni convierte disponibilidad del proveedor en inventario. Las ofertas conservan su ruta y significado propios.

Si varios productos coinciden, Saiki pide el nombre completo. Si el producto está solo en catálogo, informa que falta inventario; no lo convierte en cero. Si un producto tiene stock cero registrado, devuelve cero. Si el producto seleccionado contradice al mencionado, pide confirmación. Un dato antiguo del chat no sustituye al stock de MongoDB. Se mantienen los permisos de empresa, almacén e inventario.

## Preguntas y medición

Se ejecutaron 20 repeticiones de cada pregunta contra MongoDB real con una base temporal de prueba. El producto y sus 12.375 kg son datos sintéticos de esa base aislada, no registros de producción. Cada respuesta coincidió con esos datos; se bloquearon las llamadas a Ollama durante el ensayo y se registraron **cero llamadas al modelo**.

| Pregunta | Mediana del servicio | P95 |
|---|---:|---:|
| ¿Cuánto stock tengo de Mango Kent? | 13.25 ms | 14.80 ms |
| ¿Cuántos kilos de mango tengo? | 13.64 ms | 15.79 ms |
| Cantidad de Mango Kent | 14.34 ms | 15.91 ms |
| Dime el stock de Mango Kent | 13.23 ms | 14.47 ms |
| ¿Cuántas unidades tengo? (producto seleccionado) | 15.05 ms | 15.62 ms |

La primera consulta del primer grupo tardó 55.07 ms. Son tiempos del servicio de texto local: no incluyen transporte HTTP, captura/transcripción de voz ni carga/reproducción TTS. No se dispone de una medición previa comparable del tiempo de inferencia, por lo que no se atribuye un porcentaje de aceleración inventado. La mejora comprobada es que estas consultas ya no esperan al modelo.

El informe original está en `artifacts/saiki-cantidades.local/medicion.json`. Para reproducir:

```powershell
cd backend
..\.runtime.local\python\python.exe scripts/medir_saiki_cantidades.py
..\.runtime.local\python\python.exe -m pytest tests/test_saiki_quantities.py -q
```

El script crea y elimina únicamente una base con prefijo `psitwin_test_saiki_perf_`; no modifica producción ni necesita llamadas externas.

## Archivos

- `backend/app/services/saiki_quantities.py`: respuesta determinista y evidencia de cantidades.
- `backend/app/services/saiki_intent_router.py`: reconocimiento de preguntas de cantidad.
- `backend/app/services/saiki_service.py`: ejecución temprana sin inferencia y unidades correctas en listados.
- `backend/app/services/saiki_inventory_summary.py`: filtros autorizados y lectura concurrente de catálogo/almacenes.
- `backend/tests/test_saiki_quantities.py`: frescura, cero, ausencia, ambigüedad, aislamiento y chat engañoso.
- `backend/scripts/medir_saiki_cantidades.py`: preguntas repetidas y medición reproducible.

Regresión final: **411 pruebas backend correctas, 26 subcasos correctos y 2 integraciones optativas omitidas**. La API local se reinició después de las pruebas para cargar la mejora.
