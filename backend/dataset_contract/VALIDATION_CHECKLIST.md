# Pruebas de aceptación del dataset

Proyecto B implementará validación ejecutable offline. Cada check: nombre, passed, failures y ejemplos sin secretos. Error obligatorio implica salida no cero y paquete no válido; no cambiarlo a warning.

- [ ] Archivos/cabeceras exactos DATA_FILES; UTF-8/RFC4180, tipos/nullable/enums correctos, round-trip CSV/JSONL, sin campos DTO inventados.
- [ ] Valores de negocio satisfacen Create y servicios; Response tras reconstruir derivados/nested. Credenciales no exportadas son excepción explícita, no declarar que CSV de cuentas satisface Register/Create completo. Usar snapshot DTO/importación aislada sin app.main ni conexiones; cotejar huellas.
- [ ] PK y claves compuestas únicas; FKs existentes, mismo tenant/almacén; producto+rack, zona+nivel y producto+orden únicos; operarios/proveedores activos.
- [ ] Maestros 1/3/6/30/3/30/6/90; 90 series completas, 2192 fechas, 197280 filas de ventas/stock; calendario 2199/precios 197910. No huecos ni duplicados compensatorios.
- [ ] UTC; padres antes de hijos, creación antes de movimientos, orden<=despacho<=recepción cuando despacho existe; recepción<vencimiento; fecha estimada coherente; ventas<=2025-12-31.
- [ ] ventas/latente/perdidas enteras no negativas; observadas<=latente; perdidas=latente-ventas y stockout consistente. Cero diferente de ausencia.
- [ ] Ventas=sum SALIDA/VENTA por fecha+inventario; otras salidas separadas; no convertir reposiciones en ventas/pedidos comerciales.
- [ ] Replay apertura: stock_anterior coincide; nuevo sigue ENTRADA/SALIDA/AJUSTE absoluto; cantidad>0, stocks>=0, continuidad diaria y cierre=snapshot final.
- [ ] Entrada de recepción coincide con cantidad aceptada y referencias; una por detalle; aceptada/rechazada/recibida/estado consistentes; sumas<=solicitadas. RECIBIDA completa; PARCIAL positiva incompleta; ENVIADA sin aceptados; PENDIENTE sin recepción.
- [ ] Capacidad kg de rack tras cada evento, niveles únicos dentro de zona, refrigeración/rangos correctos; no inferir capacidad de aforo/área. Stock<=máximo por política base.
- [ ] Lotes internos perecederos sin consumo vencido; si vencimiento activado, otras salidas registradas y target backend distinto advertido.
- [ ] Calendario ISO/bisiestos/semanas y flags correctos; SNAP=0; precios>0/PEN y conocido_en antes de uso; mapping reversible sin impersonar códigos M5.
- [ ] TRAIN targets hasta 2023-12-31, VALID 2024, TEST 2025; features<=origen, exógenas conocido_en<=origen; calentamiento anual explícito, no imputación con futuro, TEST fuera de selección.
- [ ] Pruebas negativas: FK ausente, PK duplicada, SALIDA excesiva, AJUSTE interpretado como delta, rack excedido, venta negativa, tenant cruzado, recepción duplicada, precio conocido en futuro y split contaminado deben rechazarse.
- [ ] Misma seed/config/versión da SHA256 idénticos de datos/schema; seed distinta altera ruido manteniendo esquema/reglas. No timestamps reales ni autorreferencia circular en manifest.
- [ ] Reportar cuantiles, tendencia/estacionalidad/heterogeneidad y censura sin metas artificiales de WAPE. Escenarios derivados y trazables.
- [ ] Sin password/hash/token/secret/code_hash en entregables, sin PII real; correos example.com; manifest/extensiones simulado=true.
- [ ] No ejecución de modelos/entrenamiento/pipeline/SMTP/API/Mongo writes. README/manifest documentan límite de reloj, rack compartido y categorías M5.

Warnings obligatorios compatibles con un dataset válido: no hay importador CSV ni entidad ventas/pedidos clientes; corte fijo requiere replay offline; nuevas categorías no garantizan compatibilidad M5; agregación multi almacén actual defectuosa; default 30d insuficiente para lags anuales. **Validez de datos no certifica métricas de modelos previos ni demo de riesgo con reloj real.**
