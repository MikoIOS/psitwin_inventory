# Inconsistencias y limitaciones de PsiTwin

Fecha de auditoría: 2026-10-13 (America/Lima). Inspección estática del workspace real. No se ejecutó el backend, no se importó app.main, no se abrió una conexión a MongoDB, no se entrenaron modelos, no se generaron registros ni datasets. Los JSON son ejemplos documentales ilustrativos. IMPLEMENTADO significa presencia y trazabilidad en código; no acredita ejecución exitosa ni datos desplegados. NO DEFINIDA significa ausencia de restricción declarada en ese contrato; NO VERIFICABLE significa falta de evidencia de ejecución o del despliegue. INFERIDO se reserva para cardinalidades y efectos deducidos. PARCIALMENTE IMPLEMENTADO distingue código existente con componentes faltantes. NO IMPLEMENTADO se limita al alcance inspeccionado.

Consecuencias evaluadas estáticamente; no se reprodujeron contra servicios. La gravedad es evaluación técnica.

## INC-01: Modelo EmpresaDocument obsoleto respecto a persistencia

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/models/empresa_model.py:4 — id y password_hash sin ruc, frente a register_empresa id_empresa/ruc/password y fechas ISO string.
- Consecuencia: Una IA que use TypedDict insertaría documentos incompatibles.
- Recomendación FUTURA: Usar servicio actual como contrato; en futuro alinear modelo.

## INC-02: Demanda significa todas las salidas

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/repositories/movimiento_repository.py:574 — $match tipo_movimiento SALIDA sin filtrar motivo_movimiento.
- Consecuencia: MERMA/VENCIMIENTO se pronostican como consumo junto a VENTA.
- Recomendación FUTURA: Mantener esta definición actual y distinguir venta si se diseña contrato futuro.

## INC-03: Ceros rellenados no acreditan observación

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/ml/demand_history.py:228 — Calendario completo y fillna(0); resumen len>=367.
- Consecuencia: Ventana vacía puede parecer historia suficiente; sesgo por ausencia de registros.
- Recomendación FUTURA: Documentar cobertura observada separadamente en diseño futuro.

## INC-04: Ventana de riesgo 30 frente a lag anual

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/inventory_risk_service.py:99 — forecast_history_days=30; config lag_364/365/366 y rolling_mean_180.
- Consecuencia: Features NaN; missing_features valida claves, no valores.
- Recomendación FUTURA: Evaluar suficiencia antes de inferencia en trabajo posterior.

## INC-05: M5 esperado sin mapeo UUID ni calendario/precios

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/ml/feature_builder.py:1401 — pending_features -> np.nan; MLContextBuilder solo agrega 15 features numéricas.
- Consecuencia: Inferencia existente no equivale a compatibilidad semántica o precisión validada con nuevos datos.
- Recomendación FUTURA: No fabricar mapeos ni covariables; definirlos aparte si corresponde.

## INC-06: Ensamble/config no aplicado en inferencia

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/ml/predictor.py:116 — get_global_model(horizon).predict; no alpha/beta/scale/local.
- Consecuencia: Resultados difieren del ensemble documentado en config.
- Recomendación FUTURA: Describir motor actual como global direct horizon.

## INC-07: Agregados de almacén basados en rack de referencia comercial

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/repositories/producto_repository.py:105 — obtener_por_almacen selecciona productos.id_rack; consumo por id_producto sin filtro rack/almacén.
- Consecuencia: Productos distribuidos pueden quedar excluidos o incorporar salidas de otros almacenes.
- Recomendación FUTURA: En futuro agregar desde inventario y ámbito físico al corte.

## INC-08: Stock y movimiento no tienen transacción multiescritura

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/movimiento_service.py:337 — CAS stock antes de insertar movimiento; compensación CAS en excepción.
- Consecuencia: Fallo/concurrencia puede dejar stock y ledger divergentes; compensación no garantizada.
- Recomendación FUTURA: Futura transacción o mecanismo de reconciliación; no implementado ahora.

## INC-09: Validación de kg por rack tiene carrera

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/rack_service.py:267 — Carga calculada consultando inventarios antes de escritura; CAS solo por inventario.
- Consecuencia: Dos inventarios del mismo rack pueden aprobar carga y exceder capacidad.
- Recomendación FUTURA: Futuro control atómico compartido por rack.

## INC-10: Unicidad de producto/rack solo aplicación

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/inventario_service.py:99 — Consultar inventarios y luego insertar; único Mongo no declarado para pareja.
- Consecuencia: Creaciones concurrentes admiten duplicados.
- Recomendación FUTURA: Futuro índice compuesto y manejo de duplicate key.

## INC-11: Campo productos.stock sin efecto persistente

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/services/producto_service.py:145 — crear y actualizar pop stock; response stock default=0.
- Consecuencia: Cliente puede leer 0 aunque existan unidades físicas.
- Recomendación FUTURA: Usar inventario.stock_actual; no interpretar stock comercial como total.

## INC-12: Actualización de producto relaja restricciones de creación

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/dto/producto_dto.py:96 — ProductoUpdate peso/volumen/nombre/categoria/familia sin límites de creación.
- Consecuencia: Peso<=0 o textos cortos posibles; producto actualizado puede desvirtuar kg.
- Recomendación FUTURA: Futuro alinear validaciones y revalidar capacidad ocupada.

## INC-13: AJUSTE no admite poner cero

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/dto/movimiento_dto.py:37 — cantidad gt=0 y AJUSTE stock_nuevo=cantidad.
- Consecuencia: No puede corregir a cero mediante AJUSTE.
- Recomendación FUTURA: Respetar contrato actual; no enviar cantidad=0.

## INC-14: Movimientos no limitan stock_maximo

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/movimiento_service.py:206 — ENTRADA/AJUSTE verifican stock negativo y kg, no stock_maximo.
- Consecuencia: Stock puede superar máximo; sobre_stock es consulta.
- Recomendación FUTURA: No asumir máximo como barrera universal.

## INC-15: Eliminaciones sin cascada integral

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/zona_service.py:423 — Eliminar zona no comprueba racks; almacén/empresa/operario/proveedor sin revisión integral de dependencias.
- Consecuencia: Referencias huérfanas, acceso y ML pueden fallar.
- Recomendación FUTURA: Futura política explícita de borrado; no inventar cascade.

## INC-16: Alta recepción multietapa sin transacción

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/recepcion_mercaderia_service.py:277 — Inserta cabecera y después crea cada detalle/movimiento.
- Consecuencia: Fallo intermedio deja recepción parcial y efectos de stock previos.
- Recomendación FUTURA: Futura atomicidad/reanudación explícita.

## INC-17: Estado RECHAZADO no fuerza aceptada=0

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/detalle_recepcion_service.py:285 — Solo EN_EVALUACION establece 0; otros estados aceptada=recibida-rechazada.
- Consecuencia: RECHAZADO con rechazo parcial puede producir entrada.
- Recomendación FUTURA: Respetar cantidades y señalar discrepancia semántica.

## INC-18: Resolver evaluación no revalida toda relación/cupo

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/detalle_recepcion_service.py:455 — Resolver valida almacén y suma recibida; no coteja producto de inventario sustituto con detalle original ni vuelve a validar suma aceptada por orden.
- Consecuencia: Inventario alternativo del mismo almacén puede recibir producto incorrecto; exceso acumulado potencial.
- Recomendación FUTURA: Futura revalidación simétrica con crear.

## INC-19: GET riesgo puede escribir

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/controllers/inventory_risk_controller.py:84 — generar_alertas=True por defecto en individual.
- Consecuencia: Consulta cambia alertas/recomendaciones, evaluación no es pura.
- Recomendación FUTURA: Documentar efecto y usar False para lecturas futuras autorizadas.

## INC-20: Fecha verificación Empresa DTO str frente a datetime

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: ALTA.
- Evidencia: app/services/email_verification_service.py:93 — fecha_verificacion_correo=datetime.now(timezone.utc), EmpresaResponse Optional[str].
- Consecuencia: Pydantic v2 puede rechazar respuesta; registro creado con fechas string no evita discrepancia.
- Recomendación FUTURA: Futuro unificar tipo y serialización.

## INC-21: Email verificación simulado puede declarar enviado

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/services/email_verification_service.py:457 — Sin SMTP retorna MOCKED y request_verification devuelve SENT.
- Consecuencia: No acredita entrega real del código.
- Recomendación FUTURA: Distinguir estado de transporte en futura implementación.

## INC-22: Estados enum no todos alcanzables

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/services/recomendacion_service.py:424 — Enum ACEPTADA/EXPIRADA existen, tabla de transiciones no los habilita.
- Consecuencia: No asumir que todos los valores permitidos por DTO tienen operación de transición.
- Recomendación FUTURA: Usar solo grafo real.

## INC-23: Defaults de configuración sensibles en código

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/config/settings.py:49 — secret_key tiene un default literal; valor omitido en auditoría.
- Consecuencia: Riesgo si despliegue no lo sustituye; valor efectivo NO VERIFICABLE.
- Recomendación FUTURA: Revisar configuración de seguridad en trabajo separado.

## INC-24: Correo duplicado en DTO Operario

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/dto/operario_dto.py:36 — correo vuelve a anotarse en Create:56 y Update:87.
- Consecuencia: Última definición prevalece; no son dos campos JSON.
- Recomendación FUTURA: Documentar ambas líneas; futura limpieza.

## INC-25: Null de actualización puede romper invariantes

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/services/proveedor_service.py:143 — ProveedorUpdate.estado nullable pero cambios[estado].value sin guard; EmpresaUpdate ruc None .strip().
- Consecuencia: Errores 500 o valores nulos incompatibles con Response.
- Recomendación FUTURA: No enviar null en campos no tratados; futura validación explícita.

## INC-26: Historial externo antiguo no accesible al corte actual

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/ml/demand_history.py:144 — fecha_fin default hoy UTC; API no expone fecha_fin.
- Consecuencia: Movimientos 2020–2025 no alimentan ventana actual de 30 días en 2026.
- Recomendación FUTURA: Otra IA debe conocer corte del backend; no simular fechas sin contrato.

## INC-27: Promociones en documentación futura, excluidas

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: dataset_contract/GENERATION_RULES.md:15 — Documentación menciona promociones publicadas; no campo predictor promotion/discount en config/código.
- Consecuencia: Una IA que siga esa documentación contradice restricción explícita del usuario.
- Recomendación FUTURA: Excluir promociones y descuentos; no trasladar esa propuesta al motor.

## INC-28: Índices de arranque pueden fallar sin bloquear servicio

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/database/mongodb.py:64 — create_index dentro de try excepto imprime advertencia.
- Consecuencia: No se garantiza índice idempotencia disponible en producción.
- Recomendación FUTURA: Índices efectivos NO VERIFICABLE sin inspección DB.

## INC-29: JWT de empresa no valida existencia en get_current_user

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/dependencies/dependencies.py:165 — Retorna UsuarioActual directamente desde claims; operario/proveedor sí consultan DB.
- Consecuencia: Tras eliminar empresa, token puede seguir pasando dependencia; bloqueo depende de endpoint.
- Recomendación FUTURA: Futura revalidación de cuenta y revocación.

## INC-30: Aprobación recomendación actualiza estado antes de generar orden

- Estado: IMPLEMENTADO (hecho estático); consecuencias INFERIDAS salvo error explícito. Gravedad: MEDIA.
- Evidencia: app/services/recomendacion_service.py:378 — Guarda APROBADA_EMPRESA; después crea orden y detalle; compensación limitada.
- Consecuencia: Fallo puede dejar estado aprobado sin orden; APLICADA se marca antes de aprobar orden.
- Recomendación FUTURA: Futura atomicidad y reconciliación de estados.

## INC-31: Recepción duplica detalles embebidos y separados

- Estado: IMPLEMENTADO. Gravedad: MEDIA.
- Evidencia: app/repositories/recepcion_mercaderia_repository.py:18 — data.copy conserva detalles del body; service crea documentos separados y sustituye array en respuesta.
- Consecuencia: La cabecera tiene detalle de entrada desactualizado respecto a resolución/ubicación/movimientos posteriores.
- Recomendación FUTURA: Futura política de fuente única o sincronización explícita.

## INC-32: Notificación de proveedor no consulta evento previo

- Estado: IMPLEMENTADO. Gravedad: MEDIA.
- Evidencia: app/services/notification_service.py:263 — enviar_orden_proveedor usa event_id y _record upsert, pero no aplica existing ENVIADO/OMITIDO de notify_owner antes de sender.
- Consecuencia: Llamadas repetidas a validar orden ENVIADA no son permitidas, pero llamadas directas al método pueden enviar correo repetido; índice evita duplicar registro, no transporte.
- Recomendación FUTURA: Futura deduplicación del envío antes de SMTP.
