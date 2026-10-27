# PROMPT AUTOCONTENIDO - GENERADOR FINAL PSITWIN

Actua como arquitecto e ingeniero de datos. Este es el proyecto B, independiente del backend PsiTwin. Implementa el generador completo, ejecutalo, valida y entrega datos segun el contrato integro incluido debajo. No termines con solo un plan o codigo sin ejecutar. No modifiques el proyecto A, DTO, opciones o modelos. No entrenes ni ejecutes modelos/forecasting. No uses predicciones anteriores como datos ni garantices metricas.

Implementa CLI generate/validate, configuracion declarativa y seed, modulos de maestros/demanda/calendario/precios/reposicion/ledger/exportacion/validacion; pruebas positivas y negativas de consistencia y causalidad. Entrega codigo, dependencias fijadas, config, README_GENERATOR.md, output CSV/JSONL/schema/manifest/validation_report. Ejecuta generacion completa con seed20261010 y validacion; corrige fallos y reporta conteos/hashes/limitaciones. Misma seed/config debe reproducir archivos. No conectar/escribir a Mongo/API, importar automaticamente ni enviar correo. Provision de cuentas fuera de datos, sin secretos en artefactos.

Contrato: DATA_FILES manda cabeceras; DTO_SCHEMA contratos implementados; RELATIONSHIPS claves/servicios/diferencias; GENERATION_RULES simulacion y VALIDATION_CHECKLIST aceptacion. Extensiones no son DTO existentes. Ejemplos pedagogicos no son un dataset reconciliado. No inventar pedidos clientes, prioridades, campos ML en Producto, ni equivalencia con categorias M5. No ocultar fallo de agregacion multi almacen o reloj actual. El dataset historico es compatible en estructura, no garantiza funcionamiento predictivo de boosters previos.

Todos los documentos referidos estan incluidos en este archivo; puedes guardarlos localmente si te ayuda, pero no necesitas el repositorio A para adivinar campos. Si hallas una contradiccion no resoluble, explicala y no declares valido un dataset con errores. Genera y valida todo lo que no dependa de ella.


---

# DOCUMENTO INCLUIDO: DATASET_SPECIFICATION.md

# Especificación oficial del dataset PsiTwin — v1.0

Contrato entre el proyecto A (backend auditado) y el proyecto B (generador independiente). Auditoría: 2026-10-10. Esta entrega contiene únicamente documentación, no datos ni modelos entrenados.

## Alcance

Empresa alimentaria sintética: **1 empresa, 3 almacenes, 30 SKU compartidos, 3 proveedores, 6 operarios, 6 zonas, 30 racks y 90 inventarios**. Historia diaria inclusiva 2020-01-01–2025-12-31: 2.192 días y 197.280 registros de ventas. Se mantienen las cantidades solicitadas; proveedores, ubicaciones y operarios adicionales permiten representar el circuito real de reposición.

Las entidades implementadas son Empresa, Almacén, Zona, Rack, Producto, Inventario, Operario, Proveedor, OrdenReposicion, DetalleReposicion, RecepcionMercaderia, DetalleRecepcion, Alerta y Recomendacion. Existen también registros auxiliares inventario_historial, notificaciones_email y email_verifications. Riesgo, forecast, autenticación y Saiki son contratos operativos/proyecciones.

**No existe entidad Pedido de cliente ni entidad de ventas históricas.** Las órdenes de reposición representan compras, no ventas. Ventas, calendario, precios, saldos y auditoría diaria se especifican como extensiones analíticas, sin presentarlas como DTO implementados.

## Autoridad de los documentos

- DTO_SCHEMA.md: declaraciones verificadas, campos, obligatoriedad, defaults, validadores y ejemplos de entidades.
- DEFAULT_OPTIONS.md: enums, defaults y opciones libres; no atribuir listas frontend no inspeccionadas.
- RELATIONSHIPS.md: claves, relaciones, restricciones de servicio e incompatibilidades.
- FORECASTING_REQUIREMENTS.md: flujo actual, features exactas y requisitos nuevos claramente separados.
- GENERATION_RULES.md: simulación reproducible, temporal y causal.
- DATA_FILES.md: autoridad de cabeceras y tipos de archivos de intercambio.
- VALIDATION_CHECKLIST.md: aceptación ejecutable del dataset.
- CODEX_DATASET_PROMPT.md: copia autocontenida de los ocho documentos para el proyecto B.

Si cambia el código fuente, versionar este contrato y revisar sus huellas. Los ejemplos JSON son pedagógicos, **no forman un conjunto de datos reconciliado** ni deben copiarse como dataset.

## Compatibilidad y límites

La entrega B consistirá en CSV, exportaciones JSONL para MongoDB, schema, manifest, reporte de validación y código generador. **No hay importador CSV implementado.** Un archivo compatible por estructura no es un cuerpo POST: IDs y fechas se generan en el servidor; los movimientos no admiten fecha histórica en Create. Un importador futuro deberá convertir fechas a BSON, respetar referencias y provisionar cuentas por un procedimiento separado, sin secretos en el paquete.

El inventario final se deriva del saldo inicial y el ledger. No se deben reaplicar movimientos sobre el snapshot final. Alertas, recomendaciones y forecasts son resultados del backend; no se precargan predicciones ni recomendaciones inventadas.

La evaluación temporal usa TRAIN 2020–2023, VALID 2024 y TEST 2025, por fecha objetivo, con calentamiento de features anuales y sin información futura. La demanda sintética se genera independientemente de los boosters anteriores; no se promete WAPE ni métricas artificiales.

La fecha de referencia es 2025-12-31. Los endpoints actuales consultan el reloj real: en octubre de 2026 una historia terminada en 2025 tiene ceros en ventanas recientes. La entrega base permite análisis/replay offline; no garantiza demo de forecasting actual al corte histórico.

## Método y evidencia

Se revisaron contratos, servicios, repositorios, controladores, modelos, configuración, módulos ML, main, dependencias, pruebas, README y configuración/selección de modelos. La relación de fuentes y rutas está incluida más abajo. Solo hay TypedDict separados para Empresa/Almacén/Zona; las demás entidades se persisten como dict. Se contrastaron DTO con construcción de documentos, consultas y validaciones de servicios.

No se encontró frontend ni AGENTS.md en el workspace. El README referencia FRontPsy/docs/ROLES.md, que no está presente: no se certifican sus opciones. No se leyó .env ni se copian credenciales del README. No se ejecutó la aplicación, MongoDB, Ollama ni inferencia. Python/los entornos virtuales apuntan a una instalación ausente; la comprobación documental se hace estáticamente con Node. No se afirma validación runtime Pydantic.

## Fuentes auditadas y huellas SHA256

| Archivo | SHA256 |
|---|---|
| app/config/settings.py | df464dabc706ab147cec1b8ea3a99187e7b1b18292830845e420f36ac32aacf8 |
| app/config/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/controllers/alerta_controller.py | e301cf767a06699761506d82cc7ec23524bc72079576bebd8545444d301c4146 |
| app/controllers/almacen_controller.py | 1e4a8c89359cbba5bf13972ac6899383a8d0b50c39022f45fa68b493f43674b3 |
| app/controllers/detalle_recepcion_controller.py | e970324543852b23d7f99deb6a2f090c0533c67aa844a424e6c95cf80efa33a0 |
| app/controllers/detalle_reposicion_controller.py | da7220953f5f350f42fc60d8f29a64b3d3b326b4e2b20283795317484a400aaf |
| app/controllers/empresa_controller.py | 742c7e9411081e494b46e77774d7a394a3f05503cc78b93948cbc0af4bb59472 |
| app/controllers/forecast_controller.py | 45d68b127a68ddf84651376eef230ee8d58566a2cbd820de87f0331ff8d1d45d |
| app/controllers/inventario_controller.py | 712c9d395c2f95a339fa9ab0bf4fde6541b51207dfdeaff1fcd5467585d25905 |
| app/controllers/inventory_risk_controller.py | c4f8232f4bc43fa2b41f09847d82b955bae8ae1ec7c6c02245cee47fe4b35938 |
| app/controllers/movimiento_controller.py | dea6d659cd26dd3a796a473c011aafdb7435bcad14c72515a75fc186fa8d4892 |
| app/controllers/operario_controller.py | 81f72c0b0d7e7205d4a884233c30ae4c1ea98240091969439fc84e66eeec04e4 |
| app/controllers/orden_reposicion_controller.py | 4b2019646eb1abfdf0f888823755c057ef0ae1ae417c5ac974c01f524b0c89ca |
| app/controllers/producto_controller.py | 75efec9a48247ae2e65bd251fc441bd7594f678f3e40ec4fb3a084714dc1d5ee |
| app/controllers/proveedor_controller.py | fadf37a0ddb4733c14de16a11a2a8f1278331898c2f4f66128c70e3e5b0c1b28 |
| app/controllers/rack_controller.py | 840841fcb0b220156600a6c5d1049e852b23bf7a6b9f7eb0554cd8ebbdd177a5 |
| app/controllers/recepcion_mercaderia_controller.py | 6373fe2372eaab716cae27c628d74f709bddee04ca1849c11c219865ae817a6d |
| app/controllers/recomendacion_controller.py | b499164bdd66b890e5b59aa32ca32af80249dec23ff75831784012065ceba5dd |
| app/controllers/saiki_controller.py | ebc8abc2222c30b305341ce4eca026fc85789397dbeb54dc3b276cd4e00a6fef |
| app/controllers/zona_controller.py | 14672ba34bc34909941f514035add8dde5d22690986003b8a8596783701faaf5 |
| app/controllers/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/database/mongodb.py | db36378b0f6459d534892822c64dfad6ac6782c21e20b2ac2ecfb63d0f290f14 |
| app/database/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/dependencies/dependencies.py | b252f4a3de9f9427eba1569523bd51229f43c43d3ea0f7d247e93ecc9080c155 |
| app/dependencies/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/dto/alerta_dto.py | 840641616b7f0f2512fd6e2de2d058a75125423061716f5cf5263f02ba5c11f7 |
| app/dto/almacen_dto.py | adcf2a65a77636479ae2866fe4fc9f5b4a3af17b0ad91ee7929db43e71a64f8b |
| app/dto/auth_dto.py | 44daaf83c92e8498e105fa9f2f581f5fed66d74af20e3e4bafbe3d3317593f0b |
| app/dto/detalle_recepcion_dto.py | 15de41c0ab835729d24654e8a10eb2deceaaa27e0f8d0cfe47f0c344bbb9fe7f |
| app/dto/detalle_reposicion_dto.py | 4e6ec6ce8156e9a21a86a15d0a3c43213cfbb7f59f38eeaf59621520e1d693a6 |
| app/dto/email_verification_dto.py | 634f7bc283b0cf64028208b7a5ac70b85e9caa1a80b3220c96a51e33e900f6a9 |
| app/dto/empresa_dto.py | 69946c7265e91cfdac55d13ce5719a646ecc442075362666e12fe9dceba708e9 |
| app/dto/inventario_dto.py | 05fa06c127eb665d8cf5c73fdbace76179c74eb187fd8255d2b8826a6a58dd9e |
| app/dto/inventory_risk_dto.py | db79d9f2ffea80ae1c49f5bd9c6b8234cf4e40ac347f2a22d12aca202fcd406f |
| app/dto/movimiento_dto.py | d636c2ee17da7e6a89b32782c4613cd562846f61d687ea47b1b54603d809a7a7 |
| app/dto/operario_dto.py | 8dd6ac7d49f3f4e5f48eb5e2657c5a27eda5e287043777d4a93c56fd1802c0c4 |
| app/dto/orden_reposicion_dto.py | daa3469b17e406a2d2ec141528e5e65fca4ed9e311e501caa68323cd01242f23 |
| app/dto/producto_dto.py | 865271fb81034348ef95b138c06394bc06304d8697d16085d483193479dc4207 |
| app/dto/proveedor_dto.py | 58a9f25d9510397c58023f2c39095826c03739f1325d8e223017429d7a8a7c17 |
| app/dto/rack_dto.py | 9453796b18f1606c1b3251a198a8b251e56d598306958751de3c2e86edc2fd0c |
| app/dto/recepcion_mercaderia_dto.py | a97060cdd2b96bd9945208124673ac685d7cdcb1b262cbbf460ca8cab50c665e |
| app/dto/recomendacion_dto.py | 5e8aeeb4c5b634fbb8cb4437469fd854f00e115bd638dba2f6bb2cb84f4e573c |
| app/dto/saiki_dto.py | 664685f875f2ae0ce0cd25d54e7b09cc902538eb22db712b5af2d363dabd0b6f |
| app/dto/zona_dto.py | e2568d9377949e6456f76c4c2b52c272c012e71e44dab5023eaa1271d219b1dc |
| app/dto/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/main.py | 9bfe620f33fdbe4b242d86d4379c19b1640dac7eee0ec380a81c35d8bc4c013e |
| app/ml/demand_history.py | e6b5033c842e8767357f14c876dc3a3fe411c219671aaf1abc998a941f6b07a4 |
| app/ml/feature_builder.py | 7ad50bd23eab521be614b5e633a0e506dea449348e3519c3c49586753f8cca32 |
| app/ml/ml_context_builder.py | 13e6388d4af62dac50115b2a2b3d42eb4c1decd696720318b64ac14fa485fc97 |
| app/ml/model_loader.py | a77f36cffa6f9d7546cc3418dd079a8b2053f4c1f34daa0beb23db00d4d6a789 |
| app/ml/predictor.py | 1eb8e812d5c5ac4e541b191af24933f67d22603326a88d7c216c968e3436a9c7 |
| app/ml/__init__.py | 3ec7fc17fcbd75d2c33adb1b8b6c6dfac19ac167bc2c91bc2e95da16c12f7fb4 |
| app/models/almacen_model.py | 5cdc615752418d2b19fac2638ea1729682cd53a67a1364ec20cfca1f9009e9e4 |
| app/models/empresa_model.py | b3ffd8675728a403f827bdd3b6a3ca93ec3693f63e08ca53cf5e8d4da27ea9d5 |
| app/models/zona_model.py | 1545552b610c5975868fdd181d04d4ba33fd3d6a27b795ec61e01d4c5983bc2d |
| app/models/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/prompts/saiki_system_prompt.py | fbf7fb9249f0c577d2b3912abe7a09b5c9aabc430cfa3802d80ce6ca6df7d4a0 |
| app/prompts/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/repositories/alerta_repository.py | 88c251c092bda19382664b228ce8986dc3ae2ac9fa0496e3d20acabc6d8fd3cf |
| app/repositories/almacen_repository.py | c54806431d41ef5a6751e9abcde7e2004f5152c22dbb0781a4bb9e788e41bbd7 |
| app/repositories/detalle_recepcion_repository.py | 2d940a2fc3f151d7bb13990d91f9a2f2b7900163612aeaf157d7dc0d84cbb035 |
| app/repositories/detalle_reposicion_repository.py | 84a3481281850ab5e956b3eb7ca38e6858231e256375ad355378cdb2b44a1919 |
| app/repositories/empresa_repository.py | 6f96865b17b73fd747dfae13c0d7baf2d8c423c1f1141b4918ce7c5ff36f9c2e |
| app/repositories/inventario_repository.py | 29441832385b6c804e345a5628d6388ffc7f4ec76f76ea5103d0f4aadaea25eb |
| app/repositories/inventory_risk_repository.py | 9f1f97c52b9032b5a8150729d58d055aa9f8e6ab42d2f4d13b44c5ab77ae85da |
| app/repositories/movimiento_repository.py | 6d27dea283585cba81ecbf992fed573888355cbd0d4d5e31d9252d81e73eeb91 |
| app/repositories/operario_repository.py | 3281429877446032df58cf9896e859c7d636711403c95969efa16379e1145ce8 |
| app/repositories/orden_reposicion_repository.py | 20bcbe8ce5cd2c0003120fcf70e246c49db5c2b8756ae0339c9c3fc8c2b61a07 |
| app/repositories/producto_repository.py | 910323043e7b064e5963d6be66b770cf77fa5e4b26cc635ad084eeac702a78c2 |
| app/repositories/proveedor_repository.py | e70aba17c99c4e4b992ca145b5a15d674bf16219d756e6b4074c18002fb7cb38 |
| app/repositories/rack_repository.py | 3a7d8ed6801fd7e495b4193a534258c388900776b8cb1e622569ceeb9a9b556f |
| app/repositories/recepcion_mercaderia_repository.py | 06844f4e8d147538b2ccf8f5a1191fe2d6a9f1f43c3140e055fccd2367c5541e |
| app/repositories/recomendacion_repository.py | 57d026b3a6fffeab2011e297d747b881e89f7a7040e3ae067fb605275da0556f |
| app/repositories/zona_repository.py | ddd3c766ca21ec78c186b154fddcd164680627006fdd1bd4cdce5c76cc7cf67a |
| app/repositories/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/services/acceso_service.py | d14a8aebfe9cb78a55e3a138775d51ce80e9a629fab01961a7eff15a6da1e871 |
| app/services/alerta_service.py | 15a5a98dadedb95893f172391e6bfdb210ede98efa3ab437f284f8b9bab70078 |
| app/services/almacen_service.py | 716bc20f1b780681545fced91996a21aa042a9473a40dee513a950349a419d86 |
| app/services/auth_service.py | 06249c8d242d6a107136b409dcc89a0af647fe53ca5ffd593bba9ef3eda8c790 |
| app/services/cuenta_service.py | c0def2163e9786d5dc667bb6536f423e3acde732abdbbaeccb64d9e2ebfc8f05 |
| app/services/detalle_recepcion_service.py | c142cb1e652e9225a6f376886c7d65cf57fde13db4353c4347a9565d14ad5ba6 |
| app/services/detalle_reposicion_service.py | c74c757a50c665d72921bbd1a519c9a25cea605ba633a127ce951e87e92632d2 |
| app/services/email_verification_service.py | 29487398f57ee0749cce9c79c6c51d281b2e7727a651c5e19f5430c76b0ca93b |
| app/services/empresa_service.py | 3c47d4bce40c7e1e92ac0888d16e43e551c7ce818d18e353d218eec682b8b5ae |
| app/services/inventario_service.py | 5af236aa27926377721204bc7c169eee43fb425e3272cc872669cfd3ea74820d |
| app/services/inventory_risk_service.py | 8c2d32b498ec3f09df0c2e6f45c8930526e8731a0876828db445471d4c04cec4 |
| app/services/movimiento_service.py | d24d37133e2269957266fbd1e3200222cc3c0a90f7184ca962ec411e898a0faa |
| app/services/notification_service.py | 1e7e61667586f063442923b275defe5c46c135789f9abd99e54194eb3be0fc10 |
| app/services/operario_service.py | b13e4b9ee77679b6f97bb0fe1491b42df4fc3529ef5622d527e8a79500c43dbb |
| app/services/orden_reposicion_service.py | 44d37797a76a08aec2db5e332d2c5e4565e622ca4bc3409899e6c9f6d15b6a99 |
| app/services/producto_service.py | e04de8bc579f37d28ff2e9e6b5cf1f3b1b2b4b81500e9734529738e5bb93ae44 |
| app/services/proveedor_service.py | edf3491708e1744bec67409f88f056afbb6a9e34090ca22312af1387a101843f |
| app/services/rack_service.py | 4eaed6c726129c65d03cc31e4563d5ba8a1ac65a1ba035e805f0d75c2177942e |
| app/services/recepcion_mercaderia_service.py | a33d392ee7432f4e1fc2ee0dcb5fc4cc927ebe95a9e5fd5a55b426b1fc4f6d3f |
| app/services/recomendacion_service.py | b175ee8359b92de87db2b27153a8a46ddaf11d8d60c00031ebacc6abec6ce16a |
| app/services/saiki_intent_router.py | 978fabae6a489b6d22d7b5722f255e0c5ee1f72ac6e4bef807dce28d7f0e770d |
| app/services/saiki_inventory_summary.py | 016e297a01817f729cc0c9baff0e8486221f8c947cf0e36e906d4e886eb3de1c |
| app/services/saiki_responses.py | bc0ec4121dced5c9c59ba20a44e50792eae15b10f5e71dfa21a2a4906c4824f9 |
| app/services/saiki_service.py | 25be6774ed27afb2fbcc927faf5d4db6100e0fb1f65bcabc1bdd5f8f9bab6097 |
| app/services/saiki_tools.py | 1bf0bf85cbf9ce5f7ac536a0a32e349dfdd3d09fc4ceec58864e989127451a22 |
| app/services/zona_service.py | 5c6222a83ed43199c5c3cd4998cf276769e1a0f78696654607575a9673a050bf |
| app/services/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/utils/security.py | 632779541ca76144974f9c38b6926b3430c2356fe05a4e2aabb3a9c800c9ad1a |
| app/utils/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| app/__init__.py | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| tests/test_notification_service.py | aa0b4a44083257526fef12b45830f8dd5d2733da4fba843b5b784b458475f7d2 |
| tests/test_rack_asignacion.py | 147be32a66a64b1f961f9c847d97e82f5027024e6131aff22327a972f9808c28 |
| tests/test_saiki_conversation_quality.py | f6bea786382961ad0d45b0b90f0df1159c5da204111cb9e30a0a1dc925b40483 |
| tests/test_saiki_http.py | 3dcbe4d9363e1ab0a3d159f95d5d403b65ac7827d5cd9087d9b711b95b73d630 |
| tests/test_saiki_inventory_summary.py | 4eb85c7531b90f5d909e2a815389b56bd2f5df5f517055c159456d36b14af037 |
| tests/test_saiki_isolation_stdlib.py | 7c346e0735b1dc270e697652057c8d4e500d89710d1f4bbac5da311a597fbf0f |
| tests/test_saiki_mongodb_integration.py | 189c4fdddffc40e2475e1c0a75f2f81ca013dba15d54c1a769c18bfff8bb0713 |
| tests/test_saiki_native_lightgbm.py | 7cafdf5b1ff64d8debf31ae444684f881dd7d1b9a8280dd4eaf54241ac2d06b7 |
| tests/test_saiki_ollama_integration.py | 1abd784ab59a2e8319e57a22505277154ea331108bd02a812bf6f1f6e207c396 |
| tests/test_saiki_request_semantics.py | e358961a87873daf4780626b4ef9426ac0b22786eff23376dd584c0dbdb38dd3 |
| tests/test_saiki_service.py | c1b784b6d296d5010b13ca72e2eac034570d921236285c7af8fa3347424cf1db |
| README.md | 0530daca3229bd6a1f7a9ad347fe4e23d643696e5a67989d4a3735283be1f886 |
| requirements.txt | 944bb98c61efbaf6f46d7c93e40c99c1d3a167e8435443b54369a41c09adea5f |
| app/ml/models/psitwin_v3_6/config_v3_6.json | d1ed1813365a9b649092436ba63ce572553cfccd00ee14fe41ab84456d056bde |
| app/ml/models/psitwin_v3_6/selection_by_horizon.csv | 4ab713323370a106da6a32fd81eb873f6cfd49303762bfb2498188e68c1807f4 |

## Endpoints encontrados

Base /api/v1. Las rutas incluyen prefix del router cuando existe; no son autorizacion para importacion.

- `app/controllers/alerta_controller.py`: POST /alertas; GET /alertas; GET /alertas/activas; GET /alertas/empresa/{id_empresa}; GET /alertas/almacen/{id_almacen}; GET /alertas/producto/{id_producto}; GET /alertas/inventario/{id_inventario}; GET /alertas/nivel/{nivel_riesgo}; GET /alertas/{id_item}; PATCH /alertas/{id_item}/estado.

- `app/controllers/almacen_controller.py`: POST /almacenes; GET /almacenes; GET /almacenes/empresa/{id_empresa}; GET /almacenes/{id_almacen}; PUT /almacenes/{id_almacen}; DELETE /almacenes/{id_almacen}.

- `app/controllers/detalle_recepcion_controller.py`: POST /recepciones/{id_recepcion}/detalles; GET /recepciones/{id_recepcion}/detalles; GET /detalles-recepcion/{id_detalle}; POST /detalles-recepcion/{id_detalle}/resolver.

- `app/controllers/detalle_reposicion_controller.py`: POST /ordenes-reposicion/{id_orden}/detalles; GET /ordenes-reposicion/{id_orden}/detalles; GET /detalles-reposicion/{id_detalle}; PUT /detalles-reposicion/{id_detalle}; DELETE /detalles-reposicion/{id_detalle}.

- `app/controllers/empresa_controller.py`: POST /auth/register; POST /auth/login; GET /auth/me; PATCH /auth/me/password; GET /empresas/me; PUT /empresas/me; PATCH /empresas/me/password; DELETE /empresas/me; POST /empresas/{id_empresa}/correo/enviar-verificacion; POST /empresas/{id_empresa}/correo/verificar.

- `app/controllers/forecast_controller.py`: GET /forecast/debug-history/{id_inventario}; GET /forecast/debug-context/{id_inventario}; GET /forecast/debug-features/{id_inventario}; GET /forecast/debug-predict/{id_inventario}; GET /forecast/predict-7-days/{id_inventario}; GET /forecast/debug-feature-info.

- `app/controllers/inventario_controller.py`: POST /inventarios; GET /inventarios; GET /inventarios/stock-bajo; GET /inventarios/sin-stock; GET /inventarios/sobre-stock; GET /inventarios/producto/{id_producto}; GET /inventarios/rack/{id_rack}; GET /inventarios/{id_inventario}; PUT /inventarios/{id_inventario}; GET /inventarios/{id_inventario}/historial; DELETE /inventarios/{id_inventario}.

- `app/controllers/inventory_risk_controller.py`: GET /inventory-risk; GET /inventory-risk/{id_inventario}.

- `app/controllers/movimiento_controller.py`: POST /movimientos; GET /movimientos; GET /movimientos/inventario/{id_inventario}; GET /movimientos/producto/{id_producto}; GET /movimientos/rack/{id_rack}; GET /movimientos/operario/{id_operario}; GET /movimientos/tipo/{tipo_movimiento}; GET /movimientos/motivo/{motivo_movimiento}; GET /movimientos/{id_movimiento}.

- `app/controllers/operario_controller.py`: POST /operarios; GET /operarios; GET /operarios/empresa/{id_empresa}; GET /operarios/estado/{estado}; GET /operarios/turno/{turno}; GET /operarios/{id_operario}; PUT /operarios/{id_operario}; POST /operarios/{id_operario}/reset-password; POST /operarios/{id_operario}/correo/enviar-verificacion; POST /operarios/{id_operario}/correo/verificar; DELETE /operarios/{id_operario}.

- `app/controllers/orden_reposicion_controller.py`: POST /ordenes-reposicion; GET /ordenes-reposicion; GET /ordenes-reposicion/proveedor/me; GET /ordenes-reposicion/empresa/{id_empresa}; GET /ordenes-reposicion/almacen/{id_almacen}; GET /ordenes-reposicion/proveedor/{id_proveedor}; GET /ordenes-reposicion/estado/{estado}; PATCH /ordenes-reposicion/{id_orden}/validar; PATCH /ordenes-reposicion/{id_orden}/aprobar; PATCH /ordenes-reposicion/{id_orden}/enviar; PATCH /ordenes-reposicion/{id_orden}/devolver; PATCH /ordenes-reposicion/{id_orden}/reenviar; PATCH /ordenes-reposicion/{id_orden}/cancelar; POST /ordenes-reposicion/{id_orden}/despacho; GET /ordenes-reposicion/{id_orden}; PUT /ordenes-reposicion/{id_orden}; DELETE /ordenes-reposicion/{id_orden}.

- `app/controllers/producto_controller.py`: POST /productos; GET /productos; GET /productos/refrigerados; GET /productos/almacen/{id_almacen}; GET /productos/rack/{id_rack}; GET /productos/categoria/{categoria}; GET /productos/{id_producto}; PUT /productos/{id_producto}; DELETE /productos/{id_producto}.

- `app/controllers/proveedor_controller.py`: POST /proveedores; GET /proveedores; GET /proveedores/empresa/{id_empresa}; GET /proveedores/estado/{estado}; GET /proveedores/{id_proveedor}; PUT /proveedores/{id_proveedor}; POST /proveedores/{id_proveedor}/reset-password; DELETE /proveedores/{id_proveedor}; POST /proveedores/{id_proveedor}/correo/enviar-verificacion; POST /proveedores/{id_proveedor}/correo/verificar.

- `app/controllers/rack_controller.py`: POST /racks; GET /racks; GET /racks/disponibles; GET /racks/zona/{id_zona}; GET /racks/{id_rack}; PUT /racks/{id_rack}; DELETE /racks/{id_rack}.

- `app/controllers/recepcion_mercaderia_controller.py`: POST /recepciones; GET /recepciones; GET /recepciones/orden/{id_orden}; GET /recepciones/operario/{id_operario}; GET /recepciones/{id_recepcion}.

- `app/controllers/recomendacion_controller.py`: POST /recomendaciones; GET /recomendaciones; GET /recomendaciones/empresa/{id_empresa}; GET /recomendaciones/almacen/{id_almacen}; GET /recomendaciones/producto/{id_producto}; GET /recomendaciones/inventario/{id_inventario}; POST /recomendaciones/{id_recomendacion}/crear-orden; GET /recomendaciones/{id_recomendacion}; PATCH /recomendaciones/{id_recomendacion}/estado; PATCH /recomendaciones/{id_recomendacion}/validar-operario; PATCH /recomendaciones/{id_recomendacion}/aprobar-empresa; PATCH /recomendaciones/{id_recomendacion}/solicitar-cambios; PATCH /recomendaciones/{id_recomendacion}/rechazar-empresa; PATCH /recomendaciones/{id_recomendacion}/actualizar-propuesta.

- `app/controllers/saiki_controller.py`: GET /saiki/health; POST /saiki/ask; POST /saiki/chat.

- `app/controllers/zona_controller.py`: POST /zonas; GET /zonas; GET /zonas/almacen/{id_almacen}; GET /zonas/{id_zona}; PUT /zonas/{id_zona}; DELETE /zonas/{id_zona}.


---

# DOCUMENTO INCLUIDO: DTO_SCHEMA.md

# DTO_SCHEMA - entidades y contratos exactos

Auditoria estatica del codigo local. Obligatorio significa presencia, nullable significa que el tipo admite null: no son equivalentes. Response no aplica todas las restricciones de Create. IDs son strings, no UUID validados por DTO; generacion UUIDv5 propuesta. Cada declaracion exacta incluye validadores, defaults y herencia; un DTO heredado conserva campos del padre. Claves/relaciones en RELATIONSHIPS. Ejemplos de entidades al final, sin credenciales.

## TipoAlerta

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class TipoAlerta(str, Enum):
    RIESGO_STOCKOUT = "RIESGO_STOCKOUT"
    STOCK_BAJO = "STOCK_BAJO"
    SOBRESTOCK = "SOBRESTOCK"
    CONSUMO_ANOMALO = "CONSUMO_ANOMALO"
    PROXIMO_VENCIMIENTO = "PROXIMO_VENCIMIENTO"
```

## NivelRiesgo

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"
```

## EstadoAlerta

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoAlerta(str, Enum):
    ACTIVA = "ACTIVA"
    VISTA = "VISTA"
    RESUELTA = "RESUELTA"
    IGNORADA = "IGNORADA"
```

## AlertaCreate

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| tipo_alerta | TipoAlerta | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| titulo | str | Obligatorio | Field( min_length=3, max_length=150 ) |
| mensaje | str | Obligatorio | Field( min_length=3, max_length=1000 ) |
| stock_actual | float | Obligatorio | Field(ge=0) |
| dias_cobertura | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| stock_seguridad | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| punto_reposicion | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| forecast_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class AlertaCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_almacen: str
    id_inventario: str
    id_producto: str

    tipo_alerta: TipoAlerta
    nivel_riesgo: NivelRiesgo

    titulo: str = Field(
        min_length=3,
        max_length=150
    )

    mensaje: str = Field(
        min_length=3,
        max_length=1000
    )

    stock_actual: float = Field(ge=0)

    dias_cobertura: Optional[float] = Field(
        default=None,
        ge=0
    )

    stock_seguridad: Optional[float] = Field(
        default=None,
        ge=0
    )

    punto_reposicion: Optional[float] = Field(
        default=None,
        ge=0
    )

    forecast_7d: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## AlertaResponse

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_alerta | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| tipo_alerta | TipoAlerta | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| titulo | str | Obligatorio | Sin default |
| mensaje | str | Obligatorio | Sin default |
| stock_actual | float | Obligatorio | Sin default |
| dias_cobertura | Optional[float] | Omitible; nullable | None |
| stock_seguridad | Optional[float] | Omitible; nullable | None |
| punto_reposicion | Optional[float] | Omitible; nullable | None |
| forecast_7d | Optional[float] | Omitible; nullable | None |
| estado | EstadoAlerta | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |
| fecha_resolucion | Optional[datetime] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class AlertaResponse(BaseModel):
    id_alerta: str

    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    tipo_alerta: TipoAlerta
    nivel_riesgo: NivelRiesgo

    titulo: str
    mensaje: str

    stock_actual: float
    dias_cobertura: Optional[float] = None
    stock_seguridad: Optional[float] = None
    punto_reposicion: Optional[float] = None
    forecast_7d: Optional[float] = None

    estado: EstadoAlerta

    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_resolucion: Optional[datetime] = None
```

## AlertaEstadoUpdate

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoAlerta | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class AlertaEstadoUpdate(BaseModel):
    estado: EstadoAlerta
```

## AlmacenCreate

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| longitud | Decimal | Obligatorio | Field( ..., ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) |
| latitud | Decimal | Obligatorio | Field( ..., ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) |
| area_m2 | float | Obligatorio | Field( ..., gt=0 ) |
| aforo | int | Obligatorio | Field( ..., ge=0 ) |
| tipo_almacen | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class AlmacenCreate(BaseModel):

    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    longitud: Decimal = Field(
        ...,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Decimal = Field(
        ...,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: float = Field(
        ...,
        gt=0
    )

    aforo: int = Field(
        ...,
        ge=0
    )

    tipo_almacen: str = Field(
        ...,
        min_length=2,
        max_length=100
    )


# ============================================================
# ACTUALIZAR ALMACEN
# ============================================================
```

## AlmacenUpdate

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| longitud | Optional[Decimal] | Omitible; nullable | Field( default=None, ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) |
| latitud | Optional[Decimal] | Omitible; nullable | Field( default=None, ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) |
| area_m2 | Optional[float] | Omitible; nullable | Field( default=None, gt=0 ) |
| aforo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| tipo_almacen | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class AlmacenUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    longitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: Optional[float] = Field(
        default=None,
        gt=0
    )

    aforo: Optional[int] = Field(
        default=None,
        ge=0
    )

    tipo_almacen: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )


# ============================================================
# RESPONSE
#
# Acepta temporalmente:
#
# id
# o
# id_almacen
#
# Pero la API siempre devuelve "id".
# ============================================================
```

## AlmacenResponse

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id | str | Obligatorio | Field( validation_alias=AliasChoices( "id", "id_almacen" ) ) |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| longitud | Decimal | Obligatorio | Sin default |
| latitud | Decimal | Obligatorio | Sin default |
| area_m2 | float | Obligatorio | Sin default |
| aforo | int | Obligatorio | Sin default |
| tipo_almacen | str | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class AlmacenResponse(BaseModel):

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_almacen"
        )
    )

    id_empresa: str

    nombre: str

    longitud: Decimal

    latitud: Decimal

    area_m2: float

    aforo: int

    tipo_almacen: str

    fecha_creacion: datetime

    fecha_actualizacion: datetime
```

## LoginRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| correo | EmailStr | Obligatorio | Sin default |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class LoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )
```

## LoginResponse

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| access_token | str | Obligatorio | Sin default |
| token_type | str | Omitible | "bearer" |
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| empresa | EmpresaResponse | Obligatorio | Sin default |
| operario | Optional[ OperarioResponse ] | Omitible; nullable | None |
| proveedor | Optional[ ProveedorResponse ] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    # Siempre presente. Para OPERARIO:
    # la empresa a la que pertenece.
    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# GET /auth/me
# ============================================================
```

## MeResponse

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| empresa | EmpresaResponse | Obligatorio | Sin default |
| operario | Optional[ OperarioResponse ] | Omitible; nullable | None |
| proveedor | Optional[ ProveedorResponse ] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class MeResponse(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# PATCH /auth/me/password (OPERARIO / PROVEEDOR)
# ============================================================
```

## CambiarPasswordRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_actual | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| password_nueva | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class CambiarPasswordRequest(BaseModel):

    password_actual: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    password_nueva: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# POST /proveedores/{id}/reset-password
# ============================================================
```

## ResetPasswordRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class ResetPasswordRequest(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: da correo a una cuenta antigua sin correo.
    correo: Optional[EmailStr] = None


# ============================================================
# USUARIO AUTENTICADO
#
# Resultado de get_current_user.
# ============================================================
```

## UsuarioActual

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| id_almacen | Optional[str] | Omitible; nullable | None |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class UsuarioActual(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    id_empresa: str

    id_operario: Optional[str] = None

    id_almacen: Optional[str] = None

    id_proveedor: Optional[str] = None

    debe_cambiar_password: bool = False

    @property
    def es_proveedor(self) -> bool:

        return self.rol == "PROVEEDOR"

    @property
    def es_empresa(self) -> bool:

        return self.rol == "EMPRESA"

    @property
    def es_operario(self) -> bool:

        return self.rol == "OPERARIO"
```

## EstadoRecepcion

Fuente: `app/dto/detalle_recepcion_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRecepcion(str, Enum):
    CONFORME = "CONFORME"
    RECHAZADO = "RECHAZADO"
    EN_EVALUACION = "EN_EVALUACION"
```

## DetalleRecepcionCreate

Fuente: `app/dto/detalle_recepcion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| cantidad_recibida | int | Obligatorio | Field( ..., gt=0 ) |
| cantidad_rechazada | int | Omitible | Field( default=0, ge=0 ) |
| lote | str | Omitible | Field( default="SIN_LOTE", min_length=1, max_length=100 ) |
| fecha_vencimiento | datetime &#124; None | Omitible; nullable | None |
| temperatura_recepcion | float &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Omitible | ( EstadoRecepcion.CONFORME ) |
| comentario_recepcion | Optional[str] | Omitible; nullable | Field( default=None, max_length=1000 ) |
| motivo_rechazo | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class DetalleRecepcionCreate(BaseModel):
    id_detalle_reposicion: str
    id_inventario: str

    cantidad_recibida: int = Field(
        ...,
        gt=0
    )

    cantidad_rechazada: int = Field(
        default=0,
        ge=0
    )

    lote: str = Field(
        default="SIN_LOTE",
        min_length=1,
        max_length=100
    )

    fecha_vencimiento: datetime | None = None

    temperatura_recepcion: float | None = None

    estado_recepcion: EstadoRecepcion = (
        EstadoRecepcion.CONFORME
    )

    comentario_recepcion: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    motivo_rechazo: Optional[str] = Field(
        default=None,
        max_length=500
    )

    @model_validator(mode="after")
    def validar_cantidades(self):

        self.lote = self.lote.strip()

        if self.comentario_recepcion is not None:
            self.comentario_recepcion = (
                self.comentario_recepcion.strip()
            )

        if (
            self.cantidad_rechazada
            > self.cantidad_recibida
        ):
            raise ValueError(
                "La cantidad rechazada no puede "
                "ser mayor que la recibida"
            )

        if (
            self.cantidad_rechazada > 0
            and not self.motivo_rechazo
            and not self.comentario_recepcion
        ):
            raise ValueError(
                "Debe indicar el motivo u observación del rechazo"
            )

        if (
            self.estado_recepcion
            in {
                EstadoRecepcion.RECHAZADO,
                EstadoRecepcion.EN_EVALUACION
            }
            and not self.comentario_recepcion
            and not self.motivo_rechazo
        ):
            raise ValueError(
                "Debe indicar el motivo de la recepción"
            )

        return self
```

## DetalleRecepcionResponse

Fuente: `app/dto/detalle_recepcion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_recepcion | str | Obligatorio | Sin default |
| id_recepcion | str | Obligatorio | Sin default |
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| cantidad_recibida | int | Obligatorio | Sin default |
| cantidad_rechazada | int | Obligatorio | Sin default |
| cantidad_aceptada | int | Obligatorio | Sin default |
| lote | str | Omitible | "SIN_LOTE" |
| fecha_vencimiento | datetime &#124; None | Omitible; nullable | None |
| temperatura_recepcion | float &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Omitible | ( EstadoRecepcion.CONFORME ) |
| comentario_recepcion | Optional[str] | Omitible; nullable | None |
| motivo_rechazo | Optional[str] | Omitible; nullable | None |
| id_movimiento | Optional[str] | Omitible; nullable | None |
| ubicado | bool | Omitible | True |
| riesgo_antes | Optional[str] | Omitible; nullable | None |
| riesgo_despues | Optional[str] | Omitible; nullable | None |
| notificacion_final | Optional[dict] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class DetalleRecepcionResponse(BaseModel):
    id_detalle_recepcion: str
    id_recepcion: str
    id_detalle_reposicion: str
    id_inventario: str

    cantidad_recibida: int
    cantidad_rechazada: int
    cantidad_aceptada: int

    lote: str = "SIN_LOTE"
    fecha_vencimiento: datetime | None = None
    temperatura_recepcion: float | None = None
    estado_recepcion: EstadoRecepcion = (
        EstadoRecepcion.CONFORME
    )
    comentario_recepcion: Optional[str] = None

    motivo_rechazo: Optional[str] = None

    id_movimiento: Optional[str] = None

    ubicado: bool = True

    riesgo_antes: Optional[str] = None
    riesgo_despues: Optional[str] = None
    notificacion_final: Optional[dict] = None

    fecha_creacion: datetime
```

## DetalleReposicionCreate

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| cantidad_solicitada | int | Obligatorio | Field( ..., gt=0 ) |
| costo_unitario | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class DetalleReposicionCreate(BaseModel):
    id_producto: str

    cantidad_solicitada: int = Field(
        ...,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## DetalleReposicionUpdate

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_solicitada | Optional[int] | Omitible; nullable | Field( default=None, gt=0 ) |
| costo_unitario | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class DetalleReposicionUpdate(BaseModel):
    cantidad_solicitada: Optional[int] = Field(
        default=None,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## DetalleReposicionResponse

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| cantidad_solicitada | int | Obligatorio | Sin default |
| costo_unitario | Optional[float] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class DetalleReposicionResponse(BaseModel):
    id_detalle_reposicion: str
    id_orden_reposicion: str
    id_producto: str

    cantidad_solicitada: int
    costo_unitario: Optional[float] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EmailVerificationCodeRequest

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| codigo | str | Obligatorio | Field( ..., min_length=6, max_length=6, pattern=r"^\d{6}$", ) |

Declaracion y validadores exactos:

```python
class EmailVerificationCodeRequest(BaseModel):
    codigo: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )
```

## EmailVerificationSendResponse

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| status | str | Obligatorio | Sin default |
| email | str &#124; None | Omitible; nullable | None |
| remaining_seconds | int &#124; None | Omitible; nullable | None |
| reason | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class EmailVerificationSendResponse(BaseModel):
    status: str
    email: str | None = None
    remaining_seconds: int | None = None
    reason: str | None = None
```

## EmailVerificationResponse

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| verified | bool | Obligatorio | Sin default |
| status | str | Obligatorio | Sin default |
| email | str &#124; None | Omitible; nullable | None |
| attempts | int &#124; None | Omitible; nullable | None |
| remaining_attempts | int &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class EmailVerificationResponse(BaseModel):
    verified: bool
    status: str
    email: str | None = None
    attempts: int | None = None
    remaining_attempts: int | None = None
```

## EmpresaRegisterRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| ruc | str | Obligatorio | Field( ..., min_length=8, max_length=20 ) |
| sector | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| correo | EmailStr | Obligatorio | Sin default |
| telefono | str | Obligatorio | Field( ..., min_length=6, max_length=20 ) |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaRegisterRequest(BaseModel):

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    ruc: str = Field(
        ...,
        min_length=8,
        max_length=20
    )

    sector: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    telefono: str = Field(
        ...,
        min_length=6,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# LOGIN
# ============================================================
```

## EmpresaLoginRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| correo | EmailStr | Obligatorio | Sin default |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaLoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR PERFIL
# ============================================================
```

## EmpresaUpdateRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| ruc | Optional[str] | Omitible; nullable | Field( default=None, min_length=8, max_length=20 ) |
| sector | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, min_length=6, max_length=20 ) |

Declaracion y validadores exactos:

```python
class EmpresaUpdateRequest(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    ruc: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=20
    )

    sector: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=20
    )


# ============================================================
# CAMBIAR PASSWORD
# ============================================================
```

## EmpresaChangePasswordRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_actual | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| password_nueva | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaChangePasswordRequest(BaseModel):

    password_actual: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    password_nueva: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ELIMINAR EMPRESA
#
# Pedimos password como confirmacion.
# ============================================================
```

## EmpresaDeleteRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaDeleteRequest(BaseModel):

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# RESPONSE EMPRESA
# ============================================================
```

## EmpresaResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| ruc | str | Obligatorio | Sin default |
| sector | str | Obligatorio | Sin default |
| correo | EmailStr | Obligatorio | Sin default |
| telefono | str | Obligatorio | Sin default |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[str] | Omitible; nullable | None |
| fecha_creacion | str | Obligatorio | Sin default |
| fecha_actualizacion | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class EmpresaResponse(BaseModel):

    id_empresa: str

    nombre: str

    ruc: str

    sector: str

    correo: EmailStr

    telefono: str

    correo_verificado: bool = False

    fecha_verificacion_correo: Optional[str] = None

    fecha_creacion: str

    fecha_actualizacion: str


# ============================================================
# LOGIN RESPONSE
# ============================================================
```

## EmpresaLoginResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| access_token | str | Obligatorio | Sin default |
| token_type | str | Omitible | "bearer" |
| empresa | EmpresaResponse | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class EmpresaLoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    empresa: EmpresaResponse


# ============================================================
# MESSAGE
# ============================================================
```

## MessageResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| mensaje | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class MessageResponse(BaseModel):

    mensaje: str
```

## InventarioCreate

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| stock_actual | int | Obligatorio | Field( ..., ge=0 ) |
| stock_minimo | int | Omitible | Field( default=0, ge=0 ) |
| stock_maximo | int | Obligatorio | Field( ..., ge=0 ) |

Declaracion y validadores exactos:

```python
class InventarioCreate(BaseModel):

    id_producto: str

    id_rack: str

    stock_actual: int = Field(
        ...,
        ge=0
    )

    stock_minimo: int = Field(
        default=0,
        ge=0
    )

    stock_maximo: int = Field(
        ...,
        ge=0
    )

    @model_validator(mode="after")
    def validar_stocks(self):

        if self.stock_minimo > self.stock_maximo:

            raise ValueError(
                "El stock mínimo no puede ser mayor "
                "que el stock máximo"
            )

        return self


# ============================================================
# ACTUALIZAR INVENTARIO
# ============================================================
```

## InventarioUpdate

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| stock_minimo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| stock_maximo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class InventarioUpdate(BaseModel):

    # Solo límites: el stock cambia únicamente por
    # movimientos y recepciones; el rack no se cambia.

    stock_minimo: Optional[int] = Field(
        default=None,
        ge=0
    )

    stock_maximo: Optional[int] = Field(
        default=None,
        ge=0
    )


# ============================================================
# RESPONSE
# ============================================================
```

## InventarioResponse

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| stock_actual | int | Obligatorio | Sin default |
| stock_minimo | int | Obligatorio | Sin default |
| stock_maximo | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class InventarioResponse(BaseModel):

    id_inventario: str

    id_producto: str

    id_rack: str

    stock_actual: int

    stock_minimo: int

    stock_maximo: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime


# ============================================================
# HISTORIAL DE CAMBIOS
#
# GET /inventarios/{id}/historial
# ============================================================
```

## InventarioHistorialResponse

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| fecha | datetime | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| operario_nombre | Optional[str] | Omitible; nullable | None |
| accion | str | Obligatorio | Sin default |
| antes | Optional[dict] | Omitible; nullable | None |
| despues | Optional[dict] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class InventarioHistorialResponse(BaseModel):

    fecha: datetime

    id_operario: Optional[str] = None

    operario_nombre: Optional[str] = None

    # CREAR | EDITAR_LIMITES
    accion: str

    antes: Optional[dict] = None

    despues: Optional[dict] = None
```

## ConsumoInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| promedio_7d | float | Obligatorio | Field( ge=0 ) |
| promedio_14d | float | Obligatorio | Field( ge=0 ) |
| promedio_28d | float | Obligatorio | Field( ge=0 ) |
| tendencia_porcentaje | float | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ConsumoInfo(BaseModel):
    promedio_7d: float = Field(
        ge=0
    )

    promedio_14d: float = Field(
        ge=0
    )

    promedio_28d: float = Field(
        ge=0
    )

    tendencia_porcentaje: float
```

## CoberturaInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| dias | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class CoberturaInfo(BaseModel):
    dias: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## ForecastDiario

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| fecha | datetime | Obligatorio | Sin default |
| demanda_predicha | float | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class ForecastDiario(BaseModel):
    fecha: datetime

    demanda_predicha: float = Field(
        ge=0
    )
```

## ForecastInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| demanda_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| fecha_quiebre_estimada | Optional[ datetime ] | Omitible; nullable | None |
| predicciones_diarias | list[ ForecastDiario ] | Omitible | Field( default_factory=list ) |

Declaracion y validadores exactos:

```python
class ForecastInfo(BaseModel):
    demanda_7d: Optional[float] = Field(
        default=None,
        ge=0
    )

    fecha_quiebre_estimada: Optional[
        datetime
    ] = None

    predicciones_diarias: list[
        ForecastDiario
    ] = Field(
        default_factory=list
    )
```

## SeguridadInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| stock_seguridad | float | Obligatorio | Field( ge=0 ) |
| punto_reposicion | float | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class SeguridadInfo(BaseModel):
    stock_seguridad: float = Field(
        ge=0
    )

    punto_reposicion: float = Field(
        ge=0
    )
```

## RiesgoInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nivel | NivelRiesgo | Obligatorio | Sin default |
| score | float | Obligatorio | Field( ge=0, le=100 ) |

Declaracion y validadores exactos:

```python
class RiesgoInfo(BaseModel):
    nivel: NivelRiesgo

    score: float = Field(
        ge=0,
        le=100
    )
```

## ReposicionInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_minima | int | Obligatorio | Field( ge=0 ) |
| cantidad_recomendada | int | Obligatorio | Field( ge=0 ) |
| cantidad_segura | int | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class ReposicionInfo(BaseModel):
    cantidad_minima: int = Field(
        ge=0
    )

    cantidad_recomendada: int = Field(
        ge=0
    )

    cantidad_segura: int = Field(
        ge=0
    )
```

## InventoryRiskResponse

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| stock_actual | float | Obligatorio | Field( ge=0 ) |
| consumo | ConsumoInfo | Obligatorio | Sin default |
| cobertura | CoberturaInfo | Obligatorio | Sin default |
| lead_time_dias | int | Obligatorio | Field( ge=0 ) |
| forecast | ForecastInfo | Obligatorio | Sin default |
| seguridad | SeguridadInfo | Obligatorio | Sin default |
| riesgo | RiesgoInfo | Obligatorio | Sin default |
| reposicion | Optional[ ReposicionInfo ] | Omitible; nullable | None |
| explicacion | Optional[str] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class InventoryRiskResponse(BaseModel):
    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    stock_actual: float = Field(
        ge=0
    )

    consumo: ConsumoInfo

    cobertura: CoberturaInfo

    lead_time_dias: int = Field(
        ge=0
    )

    forecast: ForecastInfo

    seguridad: SeguridadInfo

    riesgo: RiesgoInfo

    reposicion: Optional[
        ReposicionInfo
    ] = None

    explicacion: Optional[str] = None
```

## TipoMovimiento

Fuente: `app/dto/movimiento_dto.py`.


Declaracion y validadores exactos:

```python
class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
```

## MotivoMovimiento

Fuente: `app/dto/movimiento_dto.py`.


Declaracion y validadores exactos:

```python
class MotivoMovimiento(str, Enum):
    RECEPCION = "RECEPCION"
    REPOSICION = "REPOSICION"
    VENTA = "VENTA"
    MERMA = "MERMA"
    VENCIMIENTO = "VENCIMIENTO"
    DEVOLUCION = "DEVOLUCION"
    CONTEO_FISICO = "CONTEO_FISICO"
    OTRO = "OTRO"
```

## MovimientoCreate

Fuente: `app/dto/movimiento_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_inventario | str | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| id_detalle_recepcion | Optional[str] | Omitible; nullable | None |
| tipo_movimiento | TipoMovimiento | Obligatorio | Sin default |
| motivo_movimiento | MotivoMovimiento | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Field(..., gt=0) |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class MovimientoCreate(BaseModel):
    id_inventario: str

    # Se fuerza al operario del token (puede omitirse).
    id_operario: Optional[str] = None

    # Interno: idempotencia de la entrada por recepción.
    id_detalle_recepcion: Optional[str] = None

    tipo_movimiento: TipoMovimiento
    motivo_movimiento: MotivoMovimiento

    cantidad: int = Field(..., gt=0)

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## MovimientoResponse

Fuente: `app/dto/movimiento_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_movimiento | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_detalle_recepcion | Optional[str] | Omitible; nullable | None |
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| id_operario | str | Obligatorio | Sin default |
| operario_nombre | Optional[str] | Omitible; nullable | None |
| id_zona | Optional[str] | Omitible; nullable | None |
| tipo_movimiento | TipoMovimiento | Obligatorio | Sin default |
| motivo_movimiento | MotivoMovimiento | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Sin default |
| stock_anterior | int | Obligatorio | Sin default |
| stock_nuevo | int | Obligatorio | Sin default |
| observacion | Optional[str] | Omitible; nullable | None |
| fecha_hora | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class MovimientoResponse(BaseModel):
    id_movimiento: str

    id_inventario: str
    id_detalle_recepcion: Optional[str] = None
    id_producto: str
    id_rack: str
    id_operario: str

    # Historial: autor y zona del rack
    operario_nombre: Optional[str] = None
    id_zona: Optional[str] = None

    tipo_movimiento: TipoMovimiento
    motivo_movimiento: MotivoMovimiento

    cantidad: int

    stock_anterior: int
    stock_nuevo: int

    observacion: Optional[str] = None

    fecha_hora: datetime
```

## OperarioCreate

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| apellido | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| correo | EmailStr | Obligatorio | Sin default |
| cargo | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| turno | str | Obligatorio | Field( ..., min_length=2, max_length=50 ) |
| estado | str | Omitible | Field( default="ACTIVO", min_length=2, max_length=50 ) |
| correo | EmailStr | Obligatorio | Sin default |
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class OperarioCreate(BaseModel):

    id_empresa: Optional[str] = None

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    apellido: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    cargo: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    turno: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    estado: str = Field(
        default="ACTIVO",
        min_length=2,
        max_length=50
    )

    correo: EmailStr

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR OPERARIO
# ============================================================
```

## OperarioUpdate

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | Optional[str] | Omitible; nullable | None |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| apellido | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| cargo | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| turno | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=50 ) |
| estado | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=50 ) |

Declaracion y validadores exactos:

```python
class OperarioUpdate(BaseModel):

    id_almacen: Optional[str] = None

    correo: Optional[EmailStr] = None

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    apellido: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    cargo: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    turno: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    estado: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# ============================================================
```

## OperarioResetPassword

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class OperarioResetPassword(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: permite dar correo a un operario
    # antiguo sin cuenta en la misma llamada.
    correo: Optional[EmailStr] = None


# ============================================================
# RESPONSE
#
# Nunca incluye el hash de la contraseña.
# id_almacen / correo son opcionales para operarios
# antiguos creados antes de las cuentas.
# ============================================================
```

## OperarioResponse

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_operario | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| apellido | str | Obligatorio | Sin default |
| cargo | str | Obligatorio | Sin default |
| turno | str | Obligatorio | Sin default |
| estado | str | Obligatorio | Sin default |
| id_almacen | Optional[str] | Omitible; nullable | None |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[datetime] | Omitible; nullable | None |
| correo | Optional[str] | Omitible; nullable | None |
| tiene_cuenta | bool | Omitible | False |
| debe_cambiar_password | bool | Omitible | False |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class OperarioResponse(BaseModel):

    id_operario: str
    id_empresa: str

    nombre: str
    apellido: str
    cargo: str
    turno: str
    estado: str

    id_almacen: Optional[str] = None
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None

    correo: Optional[str] = None

    tiene_cuenta: bool = False

    debe_cambiar_password: bool = False

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EstadoOrdenReposicion

Fuente: `app/dto/orden_reposicion_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoOrdenReposicion(str, Enum):
    PENDIENTE = "PENDIENTE"
    # Devuelta por la empresa con comentario
    OBSERVADA = "OBSERVADA"
    # Solo órdenes antiguas: hoy validar pasa directo a ENVIADA
    APROBADA = "APROBADA"
    ENVIADA = "ENVIADA"
    PARCIAL = "PARCIAL"
    RECIBIDA = "RECIBIDA"
    CANCELADA = "CANCELADA"
```

## OrigenOrden

Fuente: `app/dto/orden_reposicion_dto.py`.


Declaracion y validadores exactos:

```python
class OrigenOrden(str, Enum):
    MANUAL = "MANUAL"
    RECOMENDACION_IA = "RECOMENDACION_IA"
```

## OrdenReposicionCreate

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recomendacion | Optional[str] | Omitible; nullable | None |
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | Optional[str] | Omitible; nullable | None |
| id_proveedor | str | Obligatorio | Sin default |
| lineas | list[DetalleReposicionCreate] | Omitible | [] |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| origen | OrigenOrden | Omitible | OrigenOrden.MANUAL |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class OrdenReposicionCreate(BaseModel):
    id_recomendacion: Optional[str] = None
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    # OPERARIO: se fuerza a su almacén (puede omitirse).
    id_almacen: Optional[str] = None
    id_proveedor: str

    # Líneas iniciales (opcional; también se pueden
    # agregar con POST /ordenes-reposicion/{id}/detalles)
    lineas: list[DetalleReposicionCreate] = []

    fecha_estimada_recepcion: Optional[datetime] = None

    origen: OrigenOrden = OrigenOrden.MANUAL

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## OrdenReposicionUpdate

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_proveedor | Optional[str] | Omitible; nullable | None |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class OrdenReposicionUpdate(BaseModel):
    id_proveedor: Optional[str] = None
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## OrdenReposicionResponse

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_recomendacion | Optional[str] | Omitible; nullable | None |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_proveedor | str | Obligatorio | Sin default |
| origen | OrigenOrden | Obligatorio | Sin default |
| estado | EstadoOrdenReposicion | Obligatorio | Sin default |
| fecha_orden | datetime | Obligatorio | Sin default |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | None |
| id_operario_solicitante | Optional[str] | Omitible; nullable | None |
| comentario_empresa | Optional[str] | Omitible; nullable | None |
| despacho | Optional[dict] | Omitible; nullable | None |
| fecha_despacho | Optional[datetime] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class OrdenReposicionResponse(BaseModel):
    id_orden_reposicion: str
    id_recomendacion: Optional[str] = None

    id_empresa: str
    id_almacen: str
    id_proveedor: str

    origen: OrigenOrden
    estado: EstadoOrdenReposicion

    fecha_orden: datetime
    fecha_estimada_recepcion: Optional[datetime] = None

    observacion: Optional[str] = None

    # Solicitud de reposición (órdenes antiguas -> null)
    id_operario_solicitante: Optional[str] = None
    comentario_empresa: Optional[str] = None

    # Despacho registrado por el proveedor
    despacho: Optional[dict] = None
    fecha_despacho: Optional[datetime] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA)
#
# PATCH /ordenes-reposicion/{id}/devolver
# ============================================================
```

## DevolverOrdenRequest

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| comentario | str | Obligatorio | Field( ..., min_length=1, max_length=1000 ) |

Declaracion y validadores exactos:

```python
class DevolverOrdenRequest(BaseModel):
    comentario: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


# ============================================================
# DESPACHO (PROVEEDOR)
#
# POST /ordenes-reposicion/{id}/despacho
# ============================================================
```

## LineaDespacho

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Field( ..., gt=0 ) |
| fecha_vencimiento | Optional[datetime] | Omitible; nullable | None |
| temperatura | Optional[float] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class LineaDespacho(BaseModel):
    id_detalle_reposicion: str

    cantidad: int = Field(
        ...,
        gt=0
    )

    fecha_vencimiento: Optional[datetime] = None

    temperatura: Optional[float] = None
```

## DespachoRequest

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| lineas | list[LineaDespacho] | Obligatorio | Field( min_length=1 ) |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class DespachoRequest(BaseModel):
    lineas: list[LineaDespacho] = Field(
        min_length=1
    )

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## ProductoCreate

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=150 ) |
| categoria | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| familia | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| marca | Optional[str] | Omitible; nullable | None |
| peso | float | Obligatorio | Field( ..., gt=0 ) |
| volumen | Optional[float] | Omitible; nullable | Field( default=None, gt=0 ) |
| stock | int | Omitible | Field( default=0, ge=0 ) |
| requiere_refrigeracion | bool | Omitible | False |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | int | Obligatorio | Field( ..., ge=0 ) |
| vida_util_dias | int | Obligatorio | Field( ..., ge=1 ) |

Declaracion y validadores exactos:

```python
class ProductoCreate(BaseModel):

    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    # Se ignora: se toma del token del PROVEEDOR.
    id_proveedor: Optional[str] = None

    # Rack de referencia: lo asigna después el OPERARIO
    # (PUT /productos/{id} {id_rack}).
    id_rack: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    categoria: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    familia: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    marca: Optional[str] = None

    # Obligatorio: kg por unidad (carga de los racks).
    peso: float = Field(
        ...,
        gt=0
    )

    volumen: Optional[float] = Field(
        default=None,
        gt=0
    )

    stock: int = Field(
        default=0,
        ge=0
    )

    requiere_refrigeracion: bool = False

    temperatura_min_almacenamiento: Optional[float] = None
    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: int = Field(
        ...,
        ge=0
    )

    vida_util_dias: int = Field(
        ...,
        ge=1
    )

    @model_validator(mode="after")
    def validar_refrigeracion(self):

        if self.requiere_refrigeracion:

            if (
                self.temperatura_min_almacenamiento is None
                or
                self.temperatura_max_almacenamiento is None
            ):

                raise ValueError(
                    "Si el producto requiere refrigeración, "
                    "debe indicar temperatura mínima y máxima"
                )

            if (
                self.temperatura_min_almacenamiento
                >
                self.temperatura_max_almacenamiento
            ):

                raise ValueError(
                    "La temperatura mínima no puede ser "
                    "mayor que la máxima"
                )

        return self
```

## ProductoUpdate

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | Optional[str] | Omitible; nullable | None |
| categoria | Optional[str] | Omitible; nullable | None |
| familia | Optional[str] | Omitible; nullable | None |
| marca | Optional[str] | Omitible; nullable | None |
| peso | Optional[float] | Omitible; nullable | None |
| volumen | Optional[float] | Omitible; nullable | None |
| stock | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| requiere_refrigeracion | Optional[bool] | Omitible; nullable | None |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| vida_util_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=1 ) |

Declaracion y validadores exactos:

```python
class ProductoUpdate(BaseModel):

    id_rack: Optional[str] = None

    nombre: Optional[str] = None
    categoria: Optional[str] = None
    familia: Optional[str] = None
    marca: Optional[str] = None

    peso: Optional[float] = None
    volumen: Optional[float] = None

    stock: Optional[int] = Field(
        default=None,
        ge=0
    )

    requiere_refrigeracion: Optional[bool] = None

    temperatura_min_almacenamiento: Optional[float] = None
    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: Optional[int] = Field(
        default=None,
        ge=0
    )

    vida_util_dias: Optional[int] = Field(
        default=None,
        ge=1
    )
```

## ProductoResponse

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Sin default |
| categoria | str | Obligatorio | Sin default |
| familia | str | Obligatorio | Sin default |
| marca | Optional[str] | Omitible; nullable | None |
| peso | Optional[float] | Omitible; nullable | None |
| volumen | Optional[float] | Omitible; nullable | None |
| stock | int | Omitible | 0 |
| requiere_refrigeracion | bool | Omitible | False |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | int | Obligatorio | Sin default |
| vida_util_dias | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ProductoResponse(BaseModel):

    id_producto: str

    id_empresa: str

    # Productos antiguos (creados por la empresa) -> null
    id_proveedor: Optional[str] = None

    # Rack de referencia (opcional)
    id_rack: Optional[str] = None

    nombre: str

    categoria: str

    familia: str

    marca: Optional[str] = None

    peso: Optional[float] = None

    volumen: Optional[float] = None

    # Para compatibilidad con registros antiguos
    stock: int = 0

    requiere_refrigeracion: bool = False

    temperatura_min_almacenamiento: Optional[float] = None

    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: int

    vida_util_dias: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime
```

## EstadoProveedor

Fuente: `app/dto/proveedor_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoProveedor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
```

## ProveedorCreate

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=150 ) |
| ruc | str | Obligatorio | Field( ..., min_length=11, max_length=11 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, max_length=20 ) |
| direccion | Optional[str] | Omitible; nullable | Field( default=None, max_length=250 ) |
| tiempo_entrega_estimado_dias | int | Omitible | Field( default=1, ge=0 ) |
| estado | EstadoProveedor | Omitible | EstadoProveedor.ACTIVO |
| password_temporal | Optional[str] | Omitible; nullable | Field( default=None, min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class ProveedorCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    ruc: str = Field(
        ...,
        min_length=11,
        max_length=11
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: int = Field(
        default=1,
        ge=0
    )

    estado: EstadoProveedor = EstadoProveedor.ACTIVO

    # Cuenta de acceso (rol PROVEEDOR). Requiere correo.
    # Queda con debe_cambiar_password = true.
    password_temporal: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128
    )
```

## ProveedorUpdate

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=150 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, max_length=20 ) |
| direccion | Optional[str] | Omitible; nullable | Field( default=None, max_length=250 ) |
| tiempo_entrega_estimado_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| estado | Optional[EstadoProveedor] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: Optional[int] = Field(
        default=None,
        ge=0
    )

    estado: Optional[EstadoProveedor] = None
```

## ProveedorResponse

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_proveedor | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| ruc | str | Obligatorio | Sin default |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| tiene_cuenta | bool | Omitible | False |
| debe_cambiar_password | bool | Omitible | False |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[datetime] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | None |
| direccion | Optional[str] | Omitible; nullable | None |
| tiempo_entrega_estimado_dias | int | Obligatorio | Sin default |
| estado | EstadoProveedor | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ProveedorResponse(BaseModel):
    id_proveedor: str
    id_empresa: str

    nombre: str
    ruc: str

    correo: Optional[EmailStr] = None
    tiene_cuenta: bool = False
    debe_cambiar_password: bool = False
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    tiempo_entrega_estimado_dias: int

    estado: EstadoProveedor

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EstadoRack

Fuente: `app/dto/rack_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRack(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    LLENO = "LLENO"
    MANTENIMIENTO = "MANTENIMIENTO"
```

## RackCreate

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_zona | str | Obligatorio | Sin default |
| codigo | str | Obligatorio | Field( min_length=1, max_length=50 ) |
| nivel | int | Obligatorio | Field( ge=1 ) |
| capacidad | float | Obligatorio | Field( gt=0 ) |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |
| estado | EstadoRack | Omitible | EstadoRack.DISPONIBLE |

Declaracion y validadores exactos:

```python
class RackCreate(BaseModel):
    id_zona: str

    codigo: str = Field(
        min_length=1,
        max_length=50
    )

    nivel: int = Field(
        ge=1
    )

    capacidad: float = Field(
        gt=0
    )

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    estado: EstadoRack = EstadoRack.DISPONIBLE

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)


# ============================================================
# EDITAR RACK (OPERARIO de ese almacén)
#
# Solo estado y temperatura.
# ============================================================
```

## RackUpdate

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoRack &#124; None | Omitible; nullable | None |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RackUpdate(BaseModel):

    estado: EstadoRack | None = None

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)
```

## RackResponse

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | str | Obligatorio | Sin default |
| id_zona | str | Obligatorio | Sin default |
| codigo | str | Obligatorio | Sin default |
| nivel | int | Obligatorio | Sin default |
| capacidad | float | Obligatorio | Sin default |
| estado | EstadoRack | Obligatorio | Sin default |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |
| carga_kg | float | Omitible | 0 |
| libre_kg | float | Omitible | 0 |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class RackResponse(BaseModel):
    id_rack: str
    id_zona: str

    codigo: str

    nivel: int

    # Carga máxima en kg
    capacidad: float

    estado: EstadoRack

    # Racks antiguos / zonas no refrigeradas -> null
    temperatura_min: float | None = None

    temperatura_max: float | None = None

    # Σ stock_actual × peso del producto
    carga_kg: float = 0

    # capacidad - carga_kg
    libre_kg: float = 0

    fecha_creacion: datetime

    fecha_actualizacion: datetime


# ============================================================
# RACK DISPONIBLE
#
# GET /racks/disponiblesiid_almacen=&id_producto=&cantidad=
# ============================================================
```

## RackDisponibleResponse

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | str | Obligatorio | Sin default |
| nombre_zona | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RackDisponibleResponse(RackResponse):

    id_almacen: str

    nombre_zona: str | None = None
```

## RecepcionMercaderiaCreate

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_operario | str &#124; None | Omitible; nullable | None |
| fecha_recepcion | datetime &#124; None | Omitible; nullable | None |
| observaciones_generales | str &#124; None | Omitible; nullable | Field( default=None, max_length=1000 ) |
| detalles | list[ DetalleRecepcionCreate ] | Obligatorio | Field(min_length=1) |

Declaracion y validadores exactos:

```python
class RecepcionMercaderiaCreate(BaseModel):

    id_orden_reposicion: str

    # OPERARIO: se fuerza al del token (puede omitirse).
    # EMPRESA: obligatorio.
    id_operario: str | None = None

    fecha_recepcion: datetime | None = None

    observaciones_generales: str | None = Field(
        default=None,
        max_length=1000
    )

    detalles: list[
        DetalleRecepcionCreate
    ] = Field(min_length=1)
```

## RecepcionMercaderiaResponse

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recepcion | str | Obligatorio | Sin default |
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_operario | str | Obligatorio | Sin default |
| fecha_recepcion | datetime | Obligatorio | Sin default |
| observaciones_generales | str &#124; None | Obligatorio; nullable | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| detalles | list[ DetalleRecepcionResponse ] | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class RecepcionMercaderiaResponse(BaseModel):

    id_recepcion: str

    id_orden_reposicion: str

    id_operario: str

    fecha_recepcion: datetime

    observaciones_generales: str | None

    fecha_creacion: datetime

    detalles: list[
        DetalleRecepcionResponse
    ]
```

## UbicarDetalleRecepcion

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class UbicarDetalleRecepcion(BaseModel):

    id_rack: str
```

## ResolverEvaluacion

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_operario | str &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Obligatorio | Sin default |
| comentario_resolucion | str | Obligatorio | Field( min_length=1, max_length=1000 ) |
| cantidad_aceptada | int &#124; None | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_rechazada | int &#124; None | Omitible; nullable | Field( default=None, ge=0 ) |
| id_inventario | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class ResolverEvaluacion(BaseModel):

    # OPERARIO: se fuerza al del token (puede omitirse).
    # EMPRESA: obligatorio.
    id_operario: str | None = None

    estado_recepcion: EstadoRecepcion

    comentario_resolucion: str = Field(
        min_length=1,
        max_length=1000
    )

    cantidad_aceptada: int | None = Field(
        default=None,
        ge=0
    )

    cantidad_rechazada: int | None = Field(
        default=None,
        ge=0
    )

    id_inventario: str | None = None

    @model_validator(mode="after")
    def validar_estado(self):

        if self.estado_recepcion not in {
            EstadoRecepcion.CONFORME,
            EstadoRecepcion.RECHAZADO
        }:
            raise ValueError(
                "Una evaluación solo puede "
                "resolverse como CONFORME "
                "o RECHAZADO"
            )

        self.comentario_resolucion = (
            self.comentario_resolucion.strip()
        )

        return self
```

## TipoRecomendacion

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class TipoRecomendacion(str, Enum):
    REABASTECER = "REABASTECER"
    NO_REABASTECER = "NO_REABASTECER"
    REDUCIR_REPOSICION = "REDUCIR_REPOSICION"
    TRASLADAR_STOCK = "TRASLADAR_STOCK"
    REVISAR_CONSUMO = "REVISAR_CONSUMO"
    REVISAR_INVENTARIO = "REVISAR_INVENTARIO"
```

## EstadoRecomendacion

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRecomendacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    VALIDADA_OPERARIO = "VALIDADA_OPERARIO"
    CAMBIOS_SOLICITADOS = "CAMBIOS_SOLICITADOS"
    APROBADA_EMPRESA = "APROBADA_EMPRESA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    APLICADA = "APLICADA"
    EXPIRADA = "EXPIRADA"
```

## RecomendacionCreate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_alerta | Optional[str] | Omitible; nullable | None |
| tipo_recomendacion | ( TipoRecomendacion ) | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| cantidad_minima | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_recomendada | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_segura | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| forecast_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| explicacion | str | Obligatorio | Field( min_length=3, max_length=3000 ) |
| origen | str | Omitible | Field( default="PSITWIN", min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class RecomendacionCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_almacen: str
    id_inventario: str
    id_producto: str

    id_alerta: Optional[str] = None

    tipo_recomendacion: (
        TipoRecomendacion
    )

    nivel_riesgo: NivelRiesgo

    cantidad_minima: Optional[int] = Field(
        default=None,
        ge=0
    )

    cantidad_recomendada: Optional[int] = Field(
        default=None,
        ge=0
    )

    cantidad_segura: Optional[int] = Field(
        default=None,
        ge=0
    )

    forecast_7d: Optional[float] = Field(
        default=None,
        ge=0
    )

    explicacion: str = Field(
        min_length=3,
        max_length=3000
    )

    origen: str = Field(
        default="PSITWIN",
        min_length=2,
        max_length=100
    )
```

## RecomendacionResponse

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recomendacion | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_alerta | Optional[str] | Omitible; nullable | None |
| tipo_recomendacion | ( TipoRecomendacion ) | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| cantidad_minima | Optional[int] | Omitible; nullable | None |
| cantidad_recomendada | Optional[int] | Omitible; nullable | None |
| cantidad_segura | Optional[int] | Omitible; nullable | None |
| forecast_7d | Optional[float] | Omitible; nullable | None |
| explicacion | str | Obligatorio | Sin default |
| origen | str | Obligatorio | Sin default |
| estado | EstadoRecomendacion | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |
| fecha_aplicacion | Optional[datetime] | Omitible; nullable | None |
| notificacion_aprobacion | Optional[dict] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RecomendacionResponse(BaseModel):
    id_recomendacion: str

    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    id_alerta: Optional[str] = None

    tipo_recomendacion: (
        TipoRecomendacion
    )

    nivel_riesgo: NivelRiesgo

    cantidad_minima: Optional[int] = None
    cantidad_recomendada: Optional[int] = None
    cantidad_segura: Optional[int] = None
    forecast_7d: Optional[float] = None

    explicacion: str
    origen: str

    estado: EstadoRecomendacion

    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_aplicacion: Optional[datetime] = None

    notificacion_aprobacion: Optional[dict] = None
```

## RecomendacionEstadoUpdate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoRecomendacion | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class RecomendacionEstadoUpdate(
    BaseModel
):
    estado: EstadoRecomendacion
```

## EmpresaCambiosRequest

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| comentario | str | Obligatorio | Field(..., min_length=1, max_length=1000) |

Declaracion y validadores exactos:

```python
class EmpresaCambiosRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    comentario: str = Field(..., min_length=1, max_length=1000)
```

## EmpresaRechazoRequest

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class EmpresaRechazoRequest(EmpresaCambiosRequest):
    pass
```

## EmpresaAprobacionRequest

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_proveedor | str | Obligatorio | Sin default |
| costo_unitario | float | Obligatorio | Field(..., ge=0) |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | Field(default=None, max_length=500) |

Declaracion y validadores exactos:

```python
class EmpresaAprobacionRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_proveedor: str
    costo_unitario: float = Field(..., ge=0)
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(default=None, max_length=500)
```

## PropuestaRecomendacionUpdate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_recomendada | Optional[int] | Omitible; nullable | Field(default=None, ge=1) |
| explicacion | Optional[str] | Omitible; nullable | Field(default=None, min_length=3, max_length=3000) |

Declaracion y validadores exactos:

```python
class PropuestaRecomendacionUpdate(BaseModel):
    cantidad_recomendada: Optional[int] = Field(default=None, ge=1)
    explicacion: Optional[str] = Field(default=None, min_length=3, max_length=3000)
```

## SaikiAskRequest

Fuente: `app/dto/saiki_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| message | str &#124; None | Omitible; nullable | Field(default=None, min_length=1) |
| question | str &#124; None | Omitible; nullable | Field( default=None, min_length=1, description="Alias legacy de message. No es necesario para nuevas consultas.", ) |
| id_inventario | str &#124; None | Omitible; nullable | None |
| id_producto | str &#124; None | Omitible; nullable | None |
| page | int | Omitible | Field(default=1, ge=1, description="Página del detalle de inventario.") |
| page_size | int | Omitible | Field(default=25, ge=1, le=100) |
| context | dict[str, Any] | Omitible | Field( default_factory=dict, description="Contexto técnico opcional; normalmente debe omitirse.", ) |
| history | list[dict[str, Any]] | Omitible | Field( default_factory=list, description="Historial opcional de mensajes previos.", ) |

Declaracion y validadores exactos:

```python
class SaikiAskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["message"],
            "examples": [
                {
                    "message": "Hola Saiki, ¿cómo está mi inventario?"
                },
                {
                    "message": "¿Qué productos tienen riesgo de quedarse sin stock?"
                },
            ],
        }
    )

    message: str | None = Field(default=None, min_length=1)
    question: str | None = Field(
        default=None,
        min_length=1,
        description="Alias legacy de message. No es necesario para nuevas consultas.",
    )
    id_inventario: str | None = None
    id_producto: str | None = None
    page: int = Field(default=1, ge=1, description="Página del detalle de inventario.")
    page_size: int = Field(default=25, ge=1, le=100)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto técnico opcional; normalmente debe omitirse.",
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historial opcional de mensajes previos.",
    )

    @model_validator(mode="after")
    def require_message(self):
        if not self.message and not self.question:
            raise ValueError("Debe indicar message o question.")
        if self.message and self.question and self.message != self.question:
            raise ValueError("message y question no pueden ser diferentes.")
        if not self.message:
            self.message = self.question
        if not self.message.strip():
            raise ValueError("message no puede contener solo espacios.")
        if len(self.history) > 40:
            raise ValueError("El historial admite hasta 40 mensajes.")
        for item in self.history:
            if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
                raise ValueError("El historial solo admite mensajes de usuario y asistente con contenido textual.")
            if len(item["content"]) > 8000:
                raise ValueError("Un mensaje del historial supera el límite de tamaño.")
            if set(item) - {"role", "content"}:
                raise ValueError("El historial no admite instrucciones de herramientas.")
        return self
```

## SaikiAskResponse

Fuente: `app/dto/saiki_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| answer | str | Obligatorio | Sin default |
| model | str | Obligatorio | Sin default |
| base_url | str | Obligatorio | Sin default |
| source | str | Omitible | "ollama" |
| context | dict[str, Any] | Omitible | Field(default_factory=dict) |
| warnings | list[str] | Omitible | Field(default_factory=list) |
| data | dict[str, Any] | Omitible | Field(default_factory=dict) |
| visualization | dict[str, Any] | Omitible | Field( default_factory=lambda: {"type": "none"} ) |
| sources | list[str] | Omitible | Field(default_factory=list) |

Declaracion y validadores exactos:

```python
class SaikiAskResponse(BaseModel):
    answer: str
    model: str
    base_url: str
    source: str = "ollama"
    context: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    visualization: dict[str, Any] = Field(
        default_factory=lambda: {"type": "none"}
    )
    sources: list[str] = Field(default_factory=list)
```

## ZonaCreate

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| tipo_zona | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| refrigerada | bool | Omitible | False |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | int | Obligatorio | Field( ..., ge=0 ) |

Declaracion y validadores exactos:

```python
class ZonaCreate(BaseModel):

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    tipo_zona: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    # Lo decide la empresa al crear la zona.
    # Solo los racks de zonas refrigeradas tienen temperatura.
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    # Cantidad de niveles (un rack por nivel).
    capacidad: int = Field(
        ...,
        ge=0
    )


# ============================================================
# ACTUALIZAR ZONA
# ============================================================
```

## ZonaUpdate

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| tipo_zona | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| refrigerada | Optional[bool] | Omitible; nullable | None |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class ZonaUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    tipo_zona: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    refrigerada: Optional[bool] = None

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: Optional[int] = Field(
        default=None,
        ge=0
    )


# ============================================================
# RESPONSE
#
# Acepta:
#
# id
# id_zona
#
# pero siempre responde como:
#
# id
# ============================================================
```

## ZonaResponse

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id | str | Obligatorio | Field( validation_alias=AliasChoices( "id", "id_zona" ) ) |
| id_almacen | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| tipo_zona | str | Obligatorio | Sin default |
| refrigerada | bool | Omitible | False |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ZonaResponse(BaseModel):

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_zona"
        )
    )

    id_almacen: str

    id_empresa: str

    nombre: str

    tipo_zona: str

    # Documentos antiguos sin el campo -> False
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime
```

## Ejemplos JSON de las 14 entidades reales

Validos por forma/declaracion Response; revision estatica, no ejecucion Pydantic. Ejemplos aislados, no un ledger reconciliado ni datos generados. No se entregan credenciales.

### EmpresaResponse

```json
{
  "id_empresa": "EMP-001",
  "nombre": "Alimentos Demo",
  "ruc": "20999999991",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "51999999001",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### AlmacenResponse

```json
{
  "id": "ALM-001",
  "id_empresa": "EMP-001",
  "nombre": "Central Lima",
  "longitud": "-77.042800",
  "latitud": "-12.046400",
  "area_m2": 1200,
  "aforo": 25,
  "tipo_almacen": "Mixto",
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ZonaResponse

```json
{
  "id": "ZON-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Zona seca",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 5,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### RackResponse

```json
{
  "id_rack": "RAC-001",
  "id_zona": "ZON-001",
  "codigo": "SECO-01",
  "nivel": 1,
  "capacidad": 5000,
  "estado": "DISPONIBLE",
  "temperatura_min": null,
  "temperatura_max": null,
  "carga_kg": 100,
  "libre_kg": 4900,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ProductoResponse

```json
{
  "id_producto": "PRO-001",
  "id_empresa": "EMP-001",
  "id_proveedor": "PRV-001",
  "id_rack": "RAC-001",
  "nombre": "Arroz 1 kg",
  "categoria": "Abarrotes",
  "familia": "Cereales",
  "marca": "Demo",
  "peso": 1,
  "volumen": null,
  "stock": 0,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 3,
  "vida_util_dias": 365,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### InventarioResponse

```json
{
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "stock_actual": 100,
  "stock_minimo": 40,
  "stock_maximo": 500,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### OperarioResponse

```json
{
  "id_operario": "OPE-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Carlos",
  "apellido": "Demo",
  "cargo": "Almacenero",
  "turno": "Manana",
  "estado": "ACTIVO",
  "correo": "operario1@example.com",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ProveedorResponse

```json
{
  "id_proveedor": "PRV-001",
  "id_empresa": "EMP-001",
  "nombre": "Distribuidora Demo",
  "ruc": "20999999992",
  "correo": null,
  "telefono": null,
  "direccion": null,
  "tiempo_entrega_estimado_dias": 3,
  "estado": "ACTIVO",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### MovimientoResponse

```json
{
  "id_movimiento": "MOV-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "id_operario": "OPE-001",
  "id_detalle_recepcion": null,
  "operario_nombre": "Carlos Demo",
  "id_zona": "ZON-001",
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 10,
  "stock_anterior": 110,
  "stock_nuevo": 100,
  "observacion": "Movimiento sintetico",
  "fecha_hora": "2025-12-31T12:00:00Z"
}
```

### OrdenReposicionResponse

```json
{
  "id_orden_reposicion": "ORD-001",
  "id_recomendacion": null,
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_proveedor": "PRV-001",
  "origen": "MANUAL",
  "estado": "RECIBIDA",
  "fecha_orden": "2025-12-20T09:00:00Z",
  "fecha_estimada_recepcion": "2025-12-23T09:00:00Z",
  "observacion": "Orden sintetica",
  "id_operario_solicitante": "OPE-001",
  "comentario_empresa": null,
  "despacho": null,
  "fecha_despacho": null,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-23T10:00:00Z"
}
```

### DetalleReposicionResponse

```json
{
  "id_detalle_reposicion": "DOR-001",
  "id_orden_reposicion": "ORD-001",
  "id_producto": "PRO-001",
  "cantidad_solicitada": 100,
  "costo_unitario": 3,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-20T09:00:00Z"
}
```

### DetalleRecepcionResponse

```json
{
  "id_detalle_recepcion": "DRE-001",
  "id_recepcion": "REC-001",
  "id_detalle_reposicion": "DOR-001",
  "id_inventario": "INV-001",
  "cantidad_recibida": 100,
  "cantidad_rechazada": 0,
  "cantidad_aceptada": 100,
  "lote": "DEMO-20251223",
  "fecha_vencimiento": "2026-12-23T00:00:00Z",
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": null,
  "motivo_rechazo": null,
  "id_movimiento": "MOV-ENT-001",
  "ubicado": true,
  "riesgo_antes": null,
  "riesgo_despues": null,
  "notificacion_final": null,
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

### AlertaResponse

```json
{
  "id_alerta": "ALE-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "tipo_alerta": "STOCK_BAJO",
  "nivel_riesgo": "ALTO",
  "titulo": "Stock bajo demo",
  "mensaje": "Stock cercano al minimo",
  "stock_actual": 20,
  "dias_cobertura": null,
  "stock_seguridad": null,
  "punto_reposicion": null,
  "forecast_7d": null,
  "estado": "ACTIVA",
  "fecha_creacion": "2025-12-31T23:59:59Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z",
  "fecha_resolucion": null
}
```

### RecomendacionResponse

```json
{
  "id_recomendacion": "RECO-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_alerta": null,
  "tipo_recomendacion": "REABASTECER",
  "nivel_riesgo": "ALTO",
  "cantidad_minima": 85,
  "cantidad_recomendada": 100,
  "cantidad_segura": 115,
  "forecast_7d": null,
  "explicacion": "Ejemplo sintetico de contrato, no inferencia ejecutada",
  "origen": "DEMO_SINTETICO",
  "estado": "PENDIENTE",
  "fecha_creacion": "2025-12-31T23:59:59Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z",
  "fecha_aplicacion": null,
  "notificacion_aprobacion": null
}
```

### RecepcionMercaderiaResponse

```json
{
  "id_recepcion": "REC-001",
  "id_orden_reposicion": "ORD-001",
  "id_operario": "OPE-001",
  "fecha_recepcion": "2025-12-23T10:00:00Z",
  "observaciones_generales": null,
  "fecha_creacion": "2025-12-23T10:00:00Z",
  "detalles": [
    {
      "id_detalle_recepcion": "DRE-001",
      "id_recepcion": "REC-001",
      "id_detalle_reposicion": "DOR-001",
      "id_inventario": "INV-001",
      "cantidad_recibida": 100,
      "cantidad_rechazada": 0,
      "cantidad_aceptada": 100,
      "lote": "DEMO-20251223",
      "fecha_vencimiento": "2026-12-23T00:00:00Z",
      "temperatura_recepcion": null,
      "estado_recepcion": "CONFORME",
      "comentario_recepcion": null,
      "motivo_rechazo": null,
      "id_movimiento": "MOV-ENT-001",
      "ubicado": true,
      "riesgo_antes": null,
      "riesgo_despues": null,
      "notificacion_final": null,
      "fecha_creacion": "2025-12-23T10:00:00Z"
    }
  ]
}
```

## Colecciones auxiliares y estructuras no autonomas

El registro `email_verifications` incluye también **cooldown_until: datetime** (now+cooldown_seconds). Su clave de upsert/consulta es entity_type+entity_id+email. status es string de flujo, sin enum Pydantic. No generar estos registros de seguridad.

- inventario_historial (InventarioRepository): id_inventario str FK, id_operario str|null FK, accion str (CREAR/EDITAR_LIMITES), antes dict|null, despues dict|null, fecha datetime. PK Mongo _id, no PK negocio; Response omite id_inventario. Ejemplo: {"id_inventario":"INV-001","id_operario":null,"accion":"CREAR","antes":null,"despues":{"stock_actual":100},"fecha":"2019-12-06T00:00:00Z"}.
- notificaciones_email (NotificationService._record): event_id str unico; id_empresa str FK, recipient str|null, subject str, status str, error str|null, fecha_creacion/fecha_actualizacion datetime. Sin DTO propio. Ejemplo: {"event_id":"APROBACION:RECO-001","id_empresa":"EMP-001","recipient":null,"subject":"Demo","status":"PENDIENTE","error":null,"fecha_creacion":"2025-12-31T00:00:00Z","fecha_actualizacion":"2025-12-31T00:00:00Z"}. No generar/enviar notificaciones.
- email_verifications (EmailVerificationService): entity_type str, entity_id str, email str, code_hash str, expires_at datetime, attempts int=0, max_attempts int por settings, used bool=false, created_at/updated_at datetime, status str inicial PENDING. Consulta por entidad/email; no asumir indice unique. No generar ni exportar codigos/hashes. Ejemplo publico valido EmailVerificationResponse: {"verified":false,"status":"NOT_FOUND"}. Los campos internos son de seguridad, no extensiones de ventas.
- Cuenta no tiene coleccion independiente comprobada; cuenta_service/auth_service gestionan credenciales en empresa/operario/proveedor. Login/UsuarioActual no son registros del dataset; tokens jamas se exportan.
- ConsumoInfo/CoberturaInfo/ForecastInfo/SeguridadInfo/RiesgoInfo/ReposicionInfo e InventoryRiskResponse son proyecciones calculadas sin repositorio de resultados de riesgo. Saiki DTO describe conversacion/visualizaciones, no entidades historicas del generador.


---

# DOCUMENTO INCLUIDO: DEFAULT_OPTIONS.md

# DEFAULT_OPTIONS - enumeraciones y valores predeterminados

No hay frontend en este repositorio; no se verificaron sus selects. Strings libres no son enums aunque se elijan valores de demo. Las enumeraciones siguientes se validan en backend Pydantic al usarse en DTO.

## TipoAlerta

Archivo: `app/dto/alerta_dto.py`.

```python
class TipoAlerta(str, Enum):
    RIESGO_STOCKOUT = "RIESGO_STOCKOUT"
    STOCK_BAJO = "STOCK_BAJO"
    SOBRESTOCK = "SOBRESTOCK"
    CONSUMO_ANOMALO = "CONSUMO_ANOMALO"
    PROXIMO_VENCIMIENTO = "PROXIMO_VENCIMIENTO"
```

## NivelRiesgo

Archivo: `app/dto/alerta_dto.py`.

```python
class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"
```

## EstadoAlerta

Archivo: `app/dto/alerta_dto.py`.

```python
class EstadoAlerta(str, Enum):
    ACTIVA = "ACTIVA"
    VISTA = "VISTA"
    RESUELTA = "RESUELTA"
    IGNORADA = "IGNORADA"
```

## EstadoRecepcion

Archivo: `app/dto/detalle_recepcion_dto.py`.

```python
class EstadoRecepcion(str, Enum):
    CONFORME = "CONFORME"
    RECHAZADO = "RECHAZADO"
    EN_EVALUACION = "EN_EVALUACION"
```

## TipoMovimiento

Archivo: `app/dto/movimiento_dto.py`.

```python
class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
```

## MotivoMovimiento

Archivo: `app/dto/movimiento_dto.py`.

```python
class MotivoMovimiento(str, Enum):
    RECEPCION = "RECEPCION"
    REPOSICION = "REPOSICION"
    VENTA = "VENTA"
    MERMA = "MERMA"
    VENCIMIENTO = "VENCIMIENTO"
    DEVOLUCION = "DEVOLUCION"
    CONTEO_FISICO = "CONTEO_FISICO"
    OTRO = "OTRO"
```

## EstadoOrdenReposicion

Archivo: `app/dto/orden_reposicion_dto.py`.

```python
class EstadoOrdenReposicion(str, Enum):
    PENDIENTE = "PENDIENTE"
    # Devuelta por la empresa con comentario
    OBSERVADA = "OBSERVADA"
    # Solo órdenes antiguas: hoy validar pasa directo a ENVIADA
    APROBADA = "APROBADA"
    ENVIADA = "ENVIADA"
    PARCIAL = "PARCIAL"
    RECIBIDA = "RECIBIDA"
    CANCELADA = "CANCELADA"
```

## OrigenOrden

Archivo: `app/dto/orden_reposicion_dto.py`.

```python
class OrigenOrden(str, Enum):
    MANUAL = "MANUAL"
    RECOMENDACION_IA = "RECOMENDACION_IA"
```

## EstadoProveedor

Archivo: `app/dto/proveedor_dto.py`.

```python
class EstadoProveedor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
```

## EstadoRack

Archivo: `app/dto/rack_dto.py`.

```python
class EstadoRack(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    LLENO = "LLENO"
    MANTENIMIENTO = "MANTENIMIENTO"
```

## TipoRecomendacion

Archivo: `app/dto/recomendacion_dto.py`.

```python
class TipoRecomendacion(str, Enum):
    REABASTECER = "REABASTECER"
    NO_REABASTECER = "NO_REABASTECER"
    REDUCIR_REPOSICION = "REDUCIR_REPOSICION"
    TRASLADAR_STOCK = "TRASLADAR_STOCK"
    REVISAR_CONSUMO = "REVISAR_CONSUMO"
    REVISAR_INVENTARIO = "REVISAR_INVENTARIO"
```

## EstadoRecomendacion

Archivo: `app/dto/recomendacion_dto.py`.

```python
class EstadoRecomendacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    VALIDADA_OPERARIO = "VALIDADA_OPERARIO"
    CAMBIOS_SOLICITADOS = "CAMBIOS_SOLICITADOS"
    APROBADA_EMPRESA = "APROBADA_EMPRESA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    APLICADA = "APLICADA"
    EXPIRADA = "EXPIRADA"
```

## Todos los defaults/restricciones declarados en DTO

| Archivo / DTO | Campo | Declaracion | Alcance |
|---|---|---|---|
| app/dto/alerta_dto.py / AlertaCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | titulo | Field( min_length=3, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | mensaje | Field( min_length=3, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | stock_actual | Field(ge=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | dias_cobertura | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | stock_seguridad | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | punto_reposicion | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | forecast_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | dias_cobertura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | stock_seguridad | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | punto_reposicion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | forecast_7d | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | fecha_resolucion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | longitud | Field( ..., ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | latitud | Field( ..., ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | area_m2 | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | aforo | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | tipo_almacen | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | longitud | Field( default=None, ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | latitud | Field( default=None, ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | area_m2 | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | aforo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | tipo_almacen | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenResponse | id | Field( validation_alias=AliasChoices( "id", "id_almacen" ) ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | token_type | "bearer" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / CambiarPasswordRequest | password_actual | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / CambiarPasswordRequest | password_nueva | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / ResetPasswordRequest | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / ResetPasswordRequest | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | cantidad_recibida | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | cantidad_rechazada | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | lote | Field( default="SIN_LOTE", min_length=1, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | temperatura_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | estado_recepcion | ( EstadoRecepcion.CONFORME ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | comentario_recepcion | Field( default=None, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | motivo_rechazo | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | lote | "SIN_LOTE" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | temperatura_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | estado_recepcion | ( EstadoRecepcion.CONFORME ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | comentario_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | motivo_rechazo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | id_movimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | ubicado | True | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | riesgo_antes | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | riesgo_despues | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | notificacion_final | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionCreate | cantidad_solicitada | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionCreate | costo_unitario | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionUpdate | cantidad_solicitada | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionUpdate | costo_unitario | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionResponse | costo_unitario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationCodeRequest | codigo | Field( ..., min_length=6, max_length=6, pattern=r"^\d{6}$", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | email | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | remaining_seconds | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | reason | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | email | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | attempts | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | remaining_attempts | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | ruc | Field( ..., min_length=8, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | sector | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | telefono | Field( ..., min_length=6, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaLoginRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | ruc | Field( default=None, min_length=8, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | sector | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | telefono | Field( default=None, min_length=6, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaChangePasswordRequest | password_actual | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaChangePasswordRequest | password_nueva | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaDeleteRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaLoginResponse | token_type | "bearer" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_actual | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_minimo | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_maximo | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioUpdate | stock_minimo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioUpdate | stock_maximo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | operario_nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | antes | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | despues | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_7d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_14d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_28d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / CoberturaInfo | dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastDiario | demanda_predicha | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | demanda_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | fecha_quiebre_estimada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | predicciones_diarias | Field( default_factory=list ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / SeguridadInfo | stock_seguridad | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / SeguridadInfo | punto_reposicion | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / RiesgoInfo | score | Field( ge=0, le=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_minima | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_recomendada | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_segura | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | stock_actual | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | lead_time_dias | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | reposicion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | explicacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | id_detalle_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | cantidad | Field(..., gt=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | id_detalle_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | operario_nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | id_zona | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | observacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | apellido | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | cargo | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | turno | Field( ..., min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | estado | Field( default="ACTIVO", min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | apellido | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | cargo | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | turno | Field( default=None, min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | estado | Field( default=None, min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResetPassword | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResetPassword | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | tiene_cuenta | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_recomendacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | lineas | [] | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | origen | OrigenOrden.MANUAL | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | id_recomendacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | observacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | id_operario_solicitante | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | comentario_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | despacho | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | fecha_despacho | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DevolverOrdenRequest | comentario | Field( ..., min_length=1, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | cantidad | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | temperatura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DespachoRequest | lineas | Field( min_length=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DespachoRequest | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | nombre | Field( ..., min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | categoria | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | familia | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | peso | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | volumen | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | stock | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | requiere_refrigeracion | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | lead_time_dias | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | vida_util_dias | Field( ..., ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | categoria | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | familia | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | peso | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | volumen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | stock | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | requiere_refrigeracion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | lead_time_dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | vida_util_dias | Field( default=None, ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | peso | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | volumen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | stock | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | requiere_refrigeracion | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | nombre | Field( ..., min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | ruc | Field( ..., min_length=11, max_length=11 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | telefono | Field( default=None, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | direccion | Field( default=None, max_length=250 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | tiempo_entrega_estimado_dias | Field( default=1, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | estado | EstadoProveedor.ACTIVO | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | password_temporal | Field( default=None, min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | nombre | Field( default=None, min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | telefono | Field( default=None, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | direccion | Field( default=None, max_length=250 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | tiempo_entrega_estimado_dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | estado | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | tiene_cuenta | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | telefono | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | direccion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | codigo | Field( min_length=1, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | nivel | Field( ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | capacidad | Field( gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | estado | EstadoRack.DISPONIBLE | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | estado | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | carga_kg | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | libre_kg | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackDisponibleResponse | nombre_zona | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | fecha_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | observaciones_generales | Field( default=None, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | detalles | Field(min_length=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | comentario_resolucion | Field( min_length=1, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | cantidad_aceptada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | cantidad_rechazada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | id_inventario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | id_alerta | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_minima | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_recomendada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_segura | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | forecast_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | explicacion | Field( min_length=3, max_length=3000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | origen | Field( default="PSITWIN", min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | id_alerta | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_minima | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_recomendada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_segura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | forecast_7d | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | fecha_aplicacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | notificacion_aprobacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaCambiosRequest | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaCambiosRequest | comentario | Field(..., min_length=1, max_length=1000) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | costo_unitario | Field(..., ge=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | observacion | Field(default=None, max_length=500) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / PropuestaRecomendacionUpdate | cantidad_recomendada | Field(default=None, ge=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / PropuestaRecomendacionUpdate | explicacion | Field(default=None, min_length=3, max_length=3000) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | message | Field(default=None, min_length=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | question | Field( default=None, min_length=1, description="Alias legacy de message. No es necesario para nuevas consultas.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | id_inventario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | id_producto | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | page | Field(default=1, ge=1, description="Página del detalle de inventario.") | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | page_size | Field(default=25, ge=1, le=100) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | context | Field( default_factory=dict, description="Contexto técnico opcional; normalmente debe omitirse.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | history | Field( default_factory=list, description="Historial opcional de mensajes previos.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | source | "ollama" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | context | Field(default_factory=dict) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | warnings | Field(default_factory=list) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | data | Field(default_factory=dict) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | visualization | Field( default_factory=lambda: {"type": "none"} ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | sources | Field(default_factory=list) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | tipo_zona | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | refrigerada | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | capacidad | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | tipo_zona | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | refrigerada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | capacidad | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | id | Field( validation_alias=AliasChoices( "id", "id_zona" ) ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | refrigerada | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |

## Opciones libres y defaults de servicios

| Campo / fuente | Valores, default y validacion |
|---|---|
| tipo_almacen, almacen_dto.py | string 2..100, obligatorio, sin catalogo backend/default; frontend no disponible |
| tipo_zona, zona_dto.py | string 2..100, obligatorio, sin catalogo/default |
| categoria/familia, producto_dto.py | string 2..100, obligatorio; sin catalogo/default |
| turno, operario_dto.py | string 2..50, obligatorio; sin enum |
| cargo, operario_dto.py | string 2..100, obligatorio |
| estado operario, operario_dto.py | string 2..50, default ACTIVO; movimientos upper()==ACTIVO; recepciones comparacion ACTIVO |
| prioridad/pedido cliente | No existe campo/DTO; no inventar |
| rol, auth_dto.py | Literal EMPRESA/OPERARIO/PROVEEDOR; backend |
| dias, demand_history.py | default 400; >0; resumen suficiente >=367 |
| dias, forecast_controller.py | default 30; 1..500 en debug-history/features/predict, 7..500 en predict-7-days |
| horizon, forecast_controller.py | default 1; 1..7 |
| ForecastArgs, saiki_tools.py | dias=30 (7..500), horizonte_dias=7 (solo 7) |
| inventory_risk_service.py | forecast_history_days=30, forecast_horizon=7, z_service_level=1.645 |
| inventory_risk_controller.py | generar_alertas=true, puede persistir salidas |
| alerta_service.py | estado inicial ACTIVA |
| recomendacion_service.py | estado inicial PENDIENTE |
| orden_reposicion_service.py | estado inicial PENDIENTE; aprobar/validar actual lleva ENVIADA |
| settings.py | api_prefix=/api/v1; email_enabled=false; verificacion TTL=10min, cooldown=60s, max_attempts=5 |

Riesgo en inventory_risk_service.py: stock<=0 CRITICO; cobertura null BAJO; cobertura<=lead positivo CRITICO; stock<=punto positivo ALTO; cobertura<=1.5*lead positivo MEDIO; resto BAJO. Seguridad=1.645*std poblacional28*sqrt(lead), consumo=max(historico reciente fallback7/14/28,forecast/7). Reposicion ceil(max(0,consumo*max(lead+7,7)+seguridad-stock)); minima ceil(0.85*q), segura ceil(1.15*q). Score combina cobertura (60/40/20 para ratio<=1/1.5/2) y stock/punto (40/30/15 para ratio<=0.5/1/1.25), maximo100.

APROBADA de orden y ACEPTADA de recomendacion son legacy; enum permitido no implica transicion valida. No hay evidencia de listas frontend. Seguridad/SMTP/Ollama/CORS no son parametros de generacion, no copiar credenciales.


---

# DOCUMENTO INCLUIDO: RELATIONSHIPS.md

# Relaciones, restricciones e incompatibilidades

MongoDB no impone FKs SQL. Son referencias lógicas verificables por el generador; no todas las rutas actuales las comprueban. UUIDv5 determinístico es una decisión del generador, no una validación de los DTO.

| Entidad / colección | PK | Referencias | Relaciones |
|---|---|---|---|
| Empresa / empresas | id_empresa | — | 1:N almacenes, productos, operarios, proveedores |
| Almacén / almacenes | id | id_empresa | 1:N zonas, operarios |
| Zona / zonas | id | id_almacen, id_empresa | 1:N racks |
| Rack / racks | id_rack | id_zona | 1:N inventarios |
| Producto / productos | id_producto | id_empresa; id_proveedor, id_rack nullable | N:M almacenes mediante inventario; rack de referencia único |
| Inventario / inventarios | id_inventario | id_producto, id_rack | Único producto+rack |
| Operario / operarios | id_operario | id_empresa; id_almacen nullable legacy | Un almacén por operario demo |
| Proveedor / proveedores | id_proveedor | id_empresa | 1:N productos, órdenes |
| OrdenReposicion / ordenes_reposicion | id_orden_reposicion | id_empresa, id_almacen, id_proveedor; id_recomendacion/id_operario_solicitante nullable | 1:N detalles y recepciones |
| DetalleReposicion / detalles_reposicion | id_detalle_reposicion | id_orden_reposicion, id_producto | Único producto por orden |
| RecepcionMercaderia / recepciones_mercaderia | id_recepcion | id_orden_reposicion, id_operario | 1:N detalles |
| DetalleRecepcion / detalles_recepcion | id_detalle_recepcion | id_recepcion, id_detalle_reposicion, id_inventario; id_movimiento nullable | Varias recepciones por línea |
| Movimiento / movimientos | id_movimiento | id_inventario, id_producto, id_rack, id_operario; id_detalle_recepcion nullable | Una entrada por detalle aceptado |
| Alerta / alertas | id_alerta | id_empresa, id_almacen, id_inventario, id_producto | N:1 inventario |
| Recomendacion / recomendaciones | id_recomendacion | mismos; id_alerta nullable | N:1 inventario; puede originar orden |

El almacén de inventario se obtiene por inventario→rack→zona→almacén, **no por Producto.id_rack**. Todas las referencias preservan empresa y almacén; proveedores/productos de una orden pertenecen al tenant. Categoría y familia son strings, no entidades.

## Restricciones verificadas en servicios

- `app/services/rack_service.py`: nivel>=1 y <=Zona.capacidad; un rack por nivel/zona. Rack.capacidad es **kg**; carga=sum(stock_actual*peso). Zona.capacidad es número de niveles. area_m2/aforo de almacén no definen capacidad de productos. El código no permite convertir aforo o área en kg.
- Temperaturas de rack solamente si zona.refrigerada; ambas obligatorias en zona refrigerada. Para producto refrigerado, rango rack contenido en rango permitido del producto. Asignación inicial exige DISPONIBLE y carga libre. Temperaturas mínimas<=máximas. `ZonaCreate` no tiene validador de rango: no atribuir al DTO esa regla.
- `inventario_service.py`: producto y rack existentes, producto+rack único, stock_minimo<=stock_maximo, stock_actual inicial<=stock_maximo y asignación física válida. Update solo modifica límites. La política demo mantendrá stock<=máximo también durante la historia; los movimientos del backend no siempre controlan ese máximo.
- `movimiento_service.py`: cantidad>0. ENTRADA motivos RECEPCION/REPOSICION/DEVOLUCION/CONTEO_FISICO/OTRO; SALIDA motivos VENTA/MERMA/VENCIMIENTO/CONTEO_FISICO/OTRO; AJUSTE motivos CONTEO_FISICO/OTRO. ENTRADA suma; SALIDA resta con stock suficiente; **AJUSTE fija stock_nuevo=cantidad**, no delta. No permite AJUSTE a cero. Incrementos validan kg con exigir_disponible=False. Operario activo obligatorio.
- `database/mongodb.py`: índice único parcial de movimientos.id_detalle_recepcion cuando es string; null no debe convertirse en string vacío. Servicio devuelve movimiento existente para idempotencia y usa actualización condicional de stock.
- `detalle_recepcion_service.py`: aceptada=recibida-rechazada en caso resuelto; EN_EVALUACION aceptada=0 y no disponible. Rechazo/evaluación requiere motivo/comentario. Suma aceptada por línea no excede solicitada. Producto del inventario coincide con línea y almacén de orden. Perfil base CONFORME sin rechazos evita ambigüedad.
- Órdenes: PENDIENTE→ENVIADA→PARCIAL→RECIBIDA, también recepción completa directa. OBSERVADA requiere comentario y reenvío; APROBADA es legacy. Proveedor ACTIVO; líneas sin productos repetidos. La aprobación actual lleva a ENVIADA.
- Recomendaciones: PENDIENTE→VALIDADA_OPERARIO→APROBADA_EMPRESA→APLICADA; CAMBIOS_SOLICITADOS vuelve a VALIDADA_OPERARIO; rechazo permitido según estado. Crear orden exige REABASTECER y cantidad>0. No basta que un enum permita un valor para que cualquier transición sea válida.
- Alertas activas se buscan por inventario+tipo y ACTIVA/VISTA. Recomendaciones pendientes se buscan por inventario+tipo y PENDIENTE/ACEPTADA; este filtro no cubre todos los estados del circuito nuevo. No precargar múltiples propuestas abiertas para ocultar esa diferencia.

## Incompatibilidades verificadas

1. `empresa_model.py`: TypedDict usa id/password_hash, omite ruc, declara fechas datetime. Servicio/repositorio real usan id_empresa/ruc/password y fechas ISO string. No usar modelo antiguo para importar.
2. Almacén: DTO Decimal con 6 decimales vs modelo/servicio float. Response devuelve id; acepta alias id_almacen. CSV canónico id; referencias siguen llamándose id_almacen.
3. `zona_model.py` omite refrigerada, que sí persiste el servicio. Response id acepta alias id_zona; repositorio admite ambos. CSV canónico id.
4. RackRepository acepta id/id_rack en algunas lecturas; otros enriquecimientos consultan exclusivamente id_rack. Generar id_rack. carga_kg/libre_kg son derivados de inventarios, no fuente de stock.
5. ProductoCreate/Update aceptan stock; ProductoService lo elimina. Response stock=0 es compatibilidad legacy. **Stock verdadero=Inventario.stock_actual**. CSV producto omite stock.
6. Producto.id_rack es una sola referencia. `ProductoRepository.obtener_por_almacen` selecciona productos por rack de referencia, no por inventarios. `MLContextBuilder` después suma movimientos por IDs de producto sin filtro de almacén: un SKU presente en tres almacenes puede omitirse de selección o mezclar almacenes en agregados store/dept. Mantener 30 SKU/90 inventarios y advertir; no duplicar SKU para esconderlo.
7. DemandHistory y riesgo agregan todas las SALIDA, no solo VENTA. Ventas históricas son extensión, sin consumidor CSV actual. Mermas/vencimientos cambiarían el objetivo implícito del modelo.
8. Identificación M5, precios, eventos/SNAP quedan NaN sin context. No existe mapeo UUID→vocabulario M5 ni consumidor precios/calendario. Nuevos datos no garantizan calidad de boosters existentes.
9. Riesgo/default API usan 30 días aunque hay lag_366/rolling_180. `missing_features` comprueba nombres, no suficiencia de datos: NaN pasa presencia.
10. Backend usa reloj actual; 2020–2025 cargado en octubre 2026 produce ceros recientes. El corte fijo del manifiesto no cambia el reloj. Se requiere replay offline o perfil desplazado separado posterior; no está implementado soporte de fecha de corte en las rutas públicas actuales.
11. APIs crean UUID/fechas actuales. MovimientoCreate no acepta fecha_hora ni stock_anterior/nuevo; POST histórico no preserva historia. Recepciones pueden disparar movimientos, riesgo/notificaciones. Exportación no equivale a replay por API.
12. OperarioCreate/Update repiten correo; Python conserva última declaración. ProductoUpdate valida menos que Create: generación siempre satisface Create y reglas de servicio.
13. Sin credenciales, EmpresaRegisterRequest y OperarioCreate no pueden recibir directamente sus CSV. Provisionar autenticación fuera de los datos; no guardar hashes/contraseñas como solución.

14. `movimiento_controller.py` restringe el POST público a **SALIDA por VENTA o VENCIMIENTO** y elimina id_detalle_recepcion del cliente. DTO/servicio permiten más motivos/tipos para operaciones internas. ENTRADA y AJUSTE del ledger no se pueden cargar mediante ese POST.

Estas diferencias se documentan, **no se corrigen ni modifican contratos en este trabajo**.


---

# DOCUMENTO INCLUIDO: FORECASTING_REQUIREMENTS.md

# Requisitos predictivos: actual y propuesta

## Implementación actual

`app/ml/demand_history.py` consulta `MovimientoRepository`, suma cantidad de todas las SALIDA por día UTC/id_inventario y rellena fechas sin salidas con 0. Devuelve DataFrame con **fecha** (datetime parseable) y **demanda** (float). No consume ventas_diarias.csv. Inventario→producto/rack→zona→almacén identifica la serie; la demanda del backend significa consumo por salidas, no demanda latente.

`FeatureBuilder` requiere fecha/demanda, ordena historial y construye calendario, lags, rolling, EWMA y cambios. `_prepare_history` conserva última fila duplicada y convierte demanda inválida a cero: el generador debe rechazar ambos errores antes de llegar ahí. std ddof=0; EWMA adjust=False. Historia recomendada>=367 días para lags anuales y>=180 para rolling/precios; calentamiento sin ceros inventados.

Detalle de alineación: `_lag(series,k)=series.iloc[-k]`; **lag_1=última observación t, igual a current_y**, no t-1. future_lag_k usa _lag(k-h) si positivo, y última observación si cero. No asumir fórmula convencional del entrenamiento anterior. Adaptador legacy futuro replica esta semántica; evaluación nueva usa y(t-k) y future_lag_k=y(t+h-k) con fecha<=t, documentando diferencia. No mezclar perfiles.

`MLContextBuilder` usa MAX_LAG=28 (29 fechas) y arma agregados store/dept/item, además de future_store/dept_lag_7. Selección de productos por rack de referencia y posterior suma por IDs sin almacén produce incompatibilidad para SKU compartidos: ver RELATIONSHIPS. No afirmar que contexto resuelve todos los datos pendientes.

`DemandPredictor` usa LightGBM global Direct Horizon D+1..D+7; recorta negativos a cero. Devuelve demanda_7d, predicciones_diarias (horizonte, fecha, demanda_predicha), no archivos ni entrenamiento. `ModelLoader` carga config_v3_6.json, selection_by_horizon.csv (pandas) y boosters nativos models/L1_FAST__global_D1.txt..D7.txt. Tiene carga de locales, pero predictor actual usa globals y no aplica automáticamente ensemble/scale de selection.

Config identifica dataset Kaggle `psitwin_m5_base_v2.pkl`: es metadata del entrenamiento anterior, **no lector pickle del backend**. No está el dataset/pipeline de entrenamiento. No existe importación histórica CSV/Parquet/XLSX en módulos auditados. Features exactas/categóricas de config se incluyen más abajo; cabecera booster global coincide con 136 features, objetivo regression_l1. Métricas M5 de config no son metas del generador.

Identificación item_id/dept_id/cat_id/store_id/state_id, precios, eventos/SNAP requieren context externo; si falta quedan NaN. Categorías se convierten con pandas category; el código no traduce UUID PsiTwin a vocabularios aprendidos M5. Los nuevos códigos de series_mapping no garantizan inferencia válida con esos boosters.

## API y recomendaciones

Base `/api/v1/forecast`: debug-history/{id_inventario}, debug-context/{id_inventario}, debug-features/{id_inventario}, debug-predict/{id_inventario}, predict-7-days/{id_inventario}, debug-feature-info. Autenticación/ámbito según controladores/acceso_service. dias default 30 (hasta 500), horizonte individual 1..7. Saiki get_forecast llama a predict_7_days; horizonte_dias solo 7.

`InventoryRiskService` consulta **30 días**, genera 7 horizontes y calcula consumo=max(media histórica con fallback 7/14/28, forecast_7d/7), cobertura, seguridad=1.645*std28*sqrt(lead), punto=consumo*lead+seguridad, cantidades para lead+7 días. Puede crear alertas/recomendaciones. 30 días no alimentan lag_366/rolling_180; missing_features solo valida presencia de claves, no calidad/suficiencia. No ejecutar estos endpoints para validar/generar datos.

Backend usa fecha actual. Cortes históricos no se inyectan desde manifest ni CSV. Una historia 2020–2025 no garantiza demanda reciente al ejecutar en octubre 2026. No generar forecast precalculado como solución.

## Extensión propuesta para trabajo ML independiente

ventas_diarias, precios, calendario y series_mapping son **fuentes nuevas sin DTO/consumidor backend**. Objetivo nuevo: ventas_observadas(t+h) por producto+almacén (una ubicación por serie demo). Demanda latente/perdidas/stockout explican censura, nunca se pasan como features observadas. Experimento latente solo separado y etiquetado.

Calendario y precios futuros utilizables únicamente si conocido_en<=origen. SNAP=0 porque no se simula ese programa; códigos de campañas sintéticas, sin afirmar feriados verificados. Agregados nuevos se filtran correctamente por almacén/familia y usan observaciones<=t; no copiar error de alcance backend a evaluación honesta.

TRAIN por fecha objetivo 2020-01-01..2023-12-31; VALID 2024-01-01..2024-12-31; TEST 2025-01-01..2025-12-31. 2020 calentamiento cuando se exigen lags anuales. Origen t, etiqueta y(t+h), h=1..7. Fila multiobjetivo que cruza corte se excluye; formato largo asigna split por target_date. Encoders/imputadores/escaladores ajustados solo TRAIN, UNKNOWN explícito. VALID/TEST pueden usar pasado observado en rolling origin, sin usar futuro al origen. TEST no selecciona modelos/semillas.

No entrenar durante generación inicial. Proyecto B entrega fuentes y opcionalmente código de preparación/evaluación, sin ejecutarlo para optimizar métricas. No exigir matriz de features materializada: las fuentes completas permiten crearla en trabajo posterior. Separar features de consumo legacy y ventas nuevas.

## Features exactas del modelo anterior

Fuente: app/ml/models/psitwin_v3_6/config_v3_6.json. 136 columnas en este orden; matriz ML, no campos Producto. Numericas salvo las categorias listadas; flags 0/1, lags/estadisticas/precios float, calendario enteros. NaN de perfil legacy no certifica suficiencia.

```text
item_id
dept_id
cat_id
store_id
state_id
month
year
dayofweek
day
weekofyear
is_weekend
has_event
quarter
dayofyear
is_month_start
is_month_end
snap
event_name_1
event_type_1
event_name_2
event_type_2
age_days
current_y
lag_1
lag_2
lag_3
lag_4
lag_5
lag_6
lag_7
lag_14
lag_21
lag_28
lag_35
lag_42
lag_56
lag_364
lag_365
lag_366
rolling_mean_3
rolling_mean_7
rolling_mean_14
rolling_mean_28
rolling_mean_56
rolling_mean_180
rolling_std_3
rolling_std_7
rolling_std_28
rolling_std_56
rolling_max_3
rolling_max_7
rolling_max_28
ewma_3
ewma_7
ewma_14
ewma_28
zero_ratio_7
zero_ratio_28
change_1_2
change_1_3
change_1_7
ratio_mean3_mean14
ratio_mean7_mean28
acceleration_3_7
acceleration_7_28
max7_vs_mean28
max3_vs_mean28
previous_7_mean
recent7_vs_previous7
dow_mean_4w
growth_streak_3
peak_count_7
rolling_inc_mean_3
rolling_inc_mean_7
rolling_inc_mean_14
rolling_inc_mean_28
rolling_inc_std_7
rolling_inc_std_28
days_since_sale
sale_rate_28
current_vs_mean7
current_vs_mean28
sell_price
price_available
price_lag_1
price_lag_7
price_change_1
price_change_7
price_mean_28
price_relative_28
price_mean_180
price_std_180
price_min_180
price_max_180
price_relative_180
price_to_max_180
price_range_position_180
store_sales_lag_1
store_sales_lag_7
store_sales_lag_28
store_sales_mean_7
store_sales_mean_28
dept_sales_lag_1
dept_sales_lag_7
dept_sales_lag_28
dept_sales_mean_7
dept_sales_mean_28
item_total_lag_1
item_total_lag_7
item_total_lag_28
target_month
target_dayofweek
target_day
target_weekofyear
target_is_weekend
target_quarter
target_dayofyear
future_sell_price
future_price_available
future_snap
future_has_event
future_event_name_1_code
future_event_type_1_code
future_lag_7
future_lag_14
future_lag_21
future_lag_28
future_lag_35
future_lag_42
future_lag_364
future_lag_365
future_lag_366
future_dow_mean_6w
future_dow_std_6w
future_store_lag_7
future_dept_lag_7
```

Categoricas: item_id, dept_id, cat_id, store_id, state_id, event_name_1, event_type_1, event_name_2, event_type_2.


---

# DOCUMENTO INCLUIDO: GENERATION_RULES.md

# Reglas de generación del proyecto B

## Escala y reproducibilidad

1 empresa, 3 almacenes (Lima/Arequipa/Trujillo ficticios), 30 SKU compartidos, 3 proveedores de 10 SKU, 6 operarios (2/almacén), 6 zonas (seca/refrigerada por almacén), 30 racks (5 niveles/zona), 90 inventarios (un SKU por almacén y una ubicación por serie). 15 SKU secos y 15 refrigerados: 3 SKU compatibles por rack. No multiplicar el catálogo por almacén.

2020-01-01..2025-12-31 inclusivo: 2192 días, 197280 ventas y snapshots diarios. Calendario/planes de precio hasta 2026-01-07 (2199 fechas), sin ventas 2026. Seed=20261010. UUIDv5 namespace fijo `a1d188f7-265c-5ebc-894a-b65ea36c236f`; nombres de clave `entidad:clave_natural`, UTF-8, publicados en README; claves por entidad y subsemillas por módulo+serie derivadas SHA256, no hash() aleatorio de proceso. Orden estable, floats redondeados, configuración/dependencias versionadas; mismos parámetros producen bytes iguales. No incluir reloj real en artefactos deterministas.

Maestros creados antes de 2020, padres antes de hijos, inventario antes del saldo inicial. UTC tanto en ledger como agrupación. reference_date=2025-12-31; no atribuir al endpoint soporte automático de esa fecha.

## Demanda y ventas

Media propuesta mu=base_producto*factor_almacén*tendencia*semana*estacionalidad_anual*campaña*efecto_precio. Parámetros de generación nuevos, no defaults backend: base 5..40 unidades/día; factor almacén 0.8..1.2; tendencia anual -3%..8%; semana 0.8..1.2; amplitud anual 0.05..0.20; campañas sintéticas 1.10..1.35 según familia. Mu>=0, Poisson o binomial negativa con dispersión moderada registrada. Choques escasos (~1% días), factor 0.7..1.4. Heterogeneidad de escalas y algunos SKU intermitentes con ceros auténticos.

No generar targets desde predicciones, seleccionar seed por métricas ni recortar variaciones para garantizar WAPE. Campañas de Navidad/verano/invierno son simulaciones, no afirmaciones de feriados oficiales. Precios positivos mensuales, cambios graduales y promociones publicadas antes de vigencia; elasticidad en configuración interna, no DTO.

Demanda latente entera>=0 se calcula **antes** de consultar stock. Ventas=min(latente,disponible); perdidas=latente-ventas; stockout=perdidas>0. No vender unidades inexistentes ni registrar SALIDA cero. La latente es una verdad del simulador, no observación ni feature disponible al modelo.

## Ledger y reposición causal

Entradas aceptadas a 09:00 UTC, ventas agregadas 12:00, otras salidas opcionales 16:00. Evitar colisiones de timestamp por inventario; ordenar fecha_hora+ID. Saldo inicial separado; inventario.csv es cierre final, no apertura. Historial CREAR conserva apertura; snapshot.fecha_actualizacion=última modificación real al corte.

Peso kg por unidad alimenticia; volumen null porque unidad no está documentada. Capacidad inicial de diseño 5000 kg/rack; comprobar carga tras **cada evento**. Si diseño insuficiente, redimensionar antes de generación y justificar manifest, sin alterar capacidad para hacer pasar un evento inválido. Zona seca sin temperaturas; refrigerada y racks 2..6 °C, productos compatibles con ese rango. area_m2=1200/aforo=25 son atributos demo, no conversión a kg.

Reposición al cierre usando ventas pasadas (media móvil 28d y std poblacional; arranque con escala base publicada). Lead producto/proveedor coherente: 3 proveedores con 2/4/7 días. Seguridad=1.645*std*sqrt(lead), punto=media*lead+seguridad, posición=stock+pendientes. Si posición<=punto, solicitar max(0,ceil(media*(lead+7)+seguridad-posición)) sujeto a kg y máximo. No usar demanda latente, ventas futuras ni forecast previo para decidir.

Cada reposición efectiva genera orden MANUAL, línea, recepción CONFORME y ENTRADA/RECEPCION enlazada. Una línea y una recepción por orden en base; cantidades positivas. Órdenes pendientes al corte sin recepción futura; fechas estimadas pueden superar corte. Proveedor y operario ACTIVO del ámbito correspondiente. Despacho opcional: si null, fecha_despacho null; si existe, respetar LineaDespacho/DespachoRequest.

Límites fijos de diseño por serie: mínimo=ceil(base*factor*lead), máximo=ceil(base*factor*(lead+21)); registrar parámetros, sin recalibrar con TEST. Stock<=máximo como política demo. Movimientos AJUSTE opcionales usan valor absoluto; base no los necesita. Recomendaciones del backend no limitan siempre por kg/máximo: no garantizar que sugerencia futura quepa sin validación.

Base sin merma/vencimiento como SALIDA: consumo backend equivale a ventas. Si se habilitan otras salidas, separarlas en inventario_diario y advertir diferencia de objetivo en manifest. Mantener ledger interno de lotes perecederos para verificar que no se consumen después de vencer; vida útil/cantidades/reposición compatibles. El backend Inventario no tiene lotes: no afirmar FEFO implementado. Si no se puede evitar vencimiento real, registrar SALIDA/VENCIMIENTO y declarar cambio de perfil/objetivo, sin ocultarlo.

## Escenarios explicables

Seleccionar políticas antes de simular: al menos 5 series candidatas a reposición retrasada, 5 de cobertura alta y 2 intermitentes; resto normal/refrigerado. Clasificar **resultado real** al corte en NORMAL/BAJO_STOCK/SIN_STOCK/SOBRESTOCK/SIN_CONSUMO/REFRIGERADO. No exigir cuotas exactas de niveles IA ni alterar cierre para cumplir etiquetas. Retrasos posponen entregas con fecha estimada coherente; sobrantes siempre<=máximo y respetan vida útil. Explicación cita política y saldo/consumo observados, no una predicción ejecutada.

## Exportación y límites

Solo archivos DATA_FILES; no entrenamiento/inferencia masiva, API/Mongo writes ni correo. Snapshot+histórico se importan sin volver a aplicar movimientos, o se reconstruye apertura+replay y se verifica igualdad. Provisionar cuentas externamente; si se reutilizan IDs existentes, remapear todas referencias consistentemente.

Posterior demo viva podría usar perfil aparte desplazando todas las fechas (maestros, movimientos, vencimientos y conocido_en) por igual cantidad de días, conservando originales 2020–2025. No forma parte de base ni arregla M5/agregaciones. No simular ventas adicionales para rellenar reloj actual sin autorización y contrato actualizado.


---

# DOCUMENTO INCLUIDO: DATA_FILES.md

# DATA_FILES - archivos y columnas exactas

CSV UTF-8, coma, cabecera exacta/orden indicado, RFC4180, decimales con punto y sin miles; int base 10, float finito, bool true/false, datetime ISO8601 UTC con Z, date YYYY-MM-DD. Celda vacia=null solamente si nullable; nunca string None/NaN. dict/list son JSON escapado en celda CSV. IDs strings estables UUIDv5 (namespace en manifest); ejemplos abreviados pedagogicos.

Exportaciones de intercambio nuevas sobre entidades reales: no son cuerpos POST ni importador existente. Aplicar restricciones Create y servicios ademas de Response. Empresa usa fechas strings ISO; el resto datetime se convierte a BSON Date para MongoDB. No generar secretos. Provision de cuentas fuera del dataset: los CSV sin password no satisfacen EmpresaRegisterRequest/OperarioCreate y no autentican por si solos. Nunca marcar tiene_cuenta=true sin una credencial valida provisionada externamente.

## empresas.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: EmpresaResponse y repositorio correspondiente. PK: id_empresa. Registros estimados: 1. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_empresa,nombre,ruc,sector,correo,telefono,correo_verificado,fecha_verificacion_correo,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| ruc | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| sector | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo | EmailStr | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| telefono | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[str] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_creacion | str | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | str | No | ISO8601 UTC; cronologia GENERATION_RULES |

## almacenes.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: AlmacenResponse y repositorio correspondiente. PK: id. Registros estimados: 3. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id,id_empresa,nombre,longitud,latitud,area_m2,aforo,tipo_almacen,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| longitud | Decimal | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| latitud | Decimal | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| area_m2 | float | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| aforo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tipo_almacen | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## zonas.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ZonaResponse y repositorio correspondiente. PK: id. Registros estimados: 6. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id,id_almacen,id_empresa,nombre,tipo_zona,refrigerada,temperatura_min,temperatura_max,capacidad,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id | str | No | Clave/referencia RELATIONSHIPS |
| id_almacen | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tipo_zona | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| refrigerada | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| capacidad | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## racks.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: RackResponse y repositorio correspondiente. PK: id_rack. Registros estimados: 30. Omitidos de Response: carga_kg, libre_kg. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_rack,id_zona,codigo,nivel,capacidad,estado,temperatura_min,temperatura_max,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| id_zona | str | No | Clave/referencia RELATIONSHIPS |
| codigo | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| nivel | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| capacidad | float | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoRack | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## proveedores.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ProveedorResponse y repositorio correspondiente. PK: id_proveedor. Registros estimados: 3. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_proveedor,id_empresa,nombre,ruc,correo,tiene_cuenta,debe_cambiar_password,correo_verificado,fecha_verificacion_correo,telefono,direccion,tiempo_entrega_estimado_dias,estado,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_proveedor | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| ruc | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo | Optional[EmailStr] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiene_cuenta | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| debe_cambiar_password | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| telefono | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| direccion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiempo_entrega_estimado_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoProveedor | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## productos.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ProductoResponse y repositorio correspondiente. PK: id_producto. Registros estimados: 30. Omitidos de Response: stock. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_producto,id_empresa,id_proveedor,id_rack,nombre,categoria,familia,marca,peso,volumen,requiere_refrigeracion,temperatura_min_almacenamiento,temperatura_max_almacenamiento,lead_time_dias,vida_util_dias,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| id_proveedor | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_rack | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| categoria | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| familia | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| marca | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| peso | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| volumen | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| requiere_refrigeracion | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min_almacenamiento | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max_almacenamiento | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| lead_time_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| vida_util_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## operarios.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: OperarioResponse y repositorio correspondiente. PK: id_operario. Registros estimados: 6. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_operario,id_empresa,nombre,apellido,cargo,turno,estado,id_almacen,correo_verificado,fecha_verificacion_correo,correo,tiene_cuenta,debe_cambiar_password,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| apellido | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cargo | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| turno | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_almacen | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| correo | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiene_cuenta | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| debe_cambiar_password | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## inventario.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: InventarioResponse y repositorio correspondiente. PK: id_inventario. Registros estimados: 90. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_inventario,id_producto,id_rack,stock_actual,stock_minimo,stock_maximo,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| stock_actual | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_minimo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_maximo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## ordenes_reposicion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: OrdenReposicionResponse y repositorio correspondiente. PK: id_orden_reposicion. Registros estimados: 20.000..40.000. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_orden_reposicion,id_recomendacion,id_empresa,id_almacen,id_proveedor,origen,estado,fecha_orden,fecha_estimada_recepcion,observacion,id_operario_solicitante,comentario_empresa,despacho,fecha_despacho,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_recomendacion | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| id_almacen | str | No | Clave/referencia RELATIONSHIPS |
| id_proveedor | str | No | Clave/referencia RELATIONSHIPS |
| origen | OrigenOrden | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoOrdenReposicion | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_orden | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_estimada_recepcion | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| observacion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_operario_solicitante | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| comentario_empresa | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| despacho | Optional[dict] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_despacho | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## detalles_reposicion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: DetalleReposicionResponse y repositorio correspondiente. PK: id_detalle_reposicion. Registros estimados: 20.000..40.000. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_detalle_reposicion,id_orden_reposicion,id_producto,cantidad_solicitada,costo_unitario,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_detalle_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| cantidad_solicitada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| costo_unitario | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## recepciones.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: RecepcionMercaderiaResponse y repositorio correspondiente. PK: id_recepcion. Registros estimados: 20.000..40.000. Omitidos de Response: detalles. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_recepcion,id_orden_reposicion,id_operario,fecha_recepcion,observaciones_generales,fecha_creacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| fecha_recepcion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| observaciones_generales | str &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## detalles_recepcion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: DetalleRecepcionResponse y repositorio correspondiente. PK: id_detalle_recepcion. Registros estimados: 20.000..40.000. Omitidos de Response: riesgo_antes, riesgo_despues, notificacion_final. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_detalle_recepcion,id_recepcion,id_detalle_reposicion,id_inventario,cantidad_recibida,cantidad_rechazada,cantidad_aceptada,lote,fecha_vencimiento,temperatura_recepcion,estado_recepcion,comentario_recepcion,motivo_rechazo,id_movimiento,ubicado,fecha_creacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_detalle_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_detalle_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| cantidad_recibida | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad_rechazada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad_aceptada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| lote | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_vencimiento | datetime &#124; None | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| temperatura_recepcion | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado_recepcion | EstadoRecepcion | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| comentario_recepcion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| motivo_rechazo | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_movimiento | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| ubicado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## movimientos.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: MovimientoResponse y repositorio correspondiente. PK: id_movimiento. Registros estimados: ~217.000..240.000. Omitidos de Response: operario_nombre, id_zona. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_movimiento,id_inventario,id_detalle_recepcion,id_producto,id_rack,id_operario,tipo_movimiento,motivo_movimiento,cantidad,stock_anterior,stock_nuevo,observacion,fecha_hora
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_movimiento | str | No | Clave/referencia RELATIONSHIPS |
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| id_detalle_recepcion | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| tipo_movimiento | TipoMovimiento | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| motivo_movimiento | MotivoMovimiento | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_anterior | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_nuevo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| observacion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_hora | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## Ejemplos de registros base (JSON equivalente a filas CSV)

### Registro empresas.csv

```json
{
  "id_empresa": "EMP-001",
  "nombre": "Alimentos Demo",
  "ruc": "20999999991",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "51999999001",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro almacenes.csv

```json
{
  "id": "ALM-001",
  "id_empresa": "EMP-001",
  "nombre": "Central Lima",
  "longitud": "-77.042800",
  "latitud": "-12.046400",
  "area_m2": 1200,
  "aforo": 25,
  "tipo_almacen": "Mixto",
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro zonas.csv

```json
{
  "id": "ZON-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Zona seca",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 5,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro racks.csv

```json
{
  "id_rack": "RAC-001",
  "id_zona": "ZON-001",
  "codigo": "SECO-01",
  "nivel": 1,
  "capacidad": 5000,
  "estado": "DISPONIBLE",
  "temperatura_min": null,
  "temperatura_max": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro productos.csv

```json
{
  "id_producto": "PRO-001",
  "id_empresa": "EMP-001",
  "id_proveedor": "PRV-001",
  "id_rack": "RAC-001",
  "nombre": "Arroz 1 kg",
  "categoria": "Abarrotes",
  "familia": "Cereales",
  "marca": "Demo",
  "peso": 1,
  "volumen": null,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 3,
  "vida_util_dias": 365,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro inventario.csv

```json
{
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "stock_actual": 100,
  "stock_minimo": 40,
  "stock_maximo": 500,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro operarios.csv

```json
{
  "id_operario": "OPE-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Carlos",
  "apellido": "Demo",
  "cargo": "Almacenero",
  "turno": "Manana",
  "estado": "ACTIVO",
  "correo": "operario1@example.com",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro proveedores.csv

```json
{
  "id_proveedor": "PRV-001",
  "id_empresa": "EMP-001",
  "nombre": "Distribuidora Demo",
  "ruc": "20999999992",
  "correo": null,
  "telefono": null,
  "direccion": null,
  "tiempo_entrega_estimado_dias": 3,
  "estado": "ACTIVO",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro movimientos.csv

```json
{
  "id_movimiento": "MOV-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "id_operario": "OPE-001",
  "id_detalle_recepcion": null,
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 10,
  "stock_anterior": 110,
  "stock_nuevo": 100,
  "observacion": "Movimiento sintetico",
  "fecha_hora": "2025-12-31T12:00:00Z"
}
```

### Registro ordenes_reposicion.csv

```json
{
  "id_orden_reposicion": "ORD-001",
  "id_recomendacion": null,
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_proveedor": "PRV-001",
  "origen": "MANUAL",
  "estado": "RECIBIDA",
  "fecha_orden": "2025-12-20T09:00:00Z",
  "fecha_estimada_recepcion": "2025-12-23T09:00:00Z",
  "observacion": "Orden sintetica",
  "id_operario_solicitante": "OPE-001",
  "comentario_empresa": null,
  "despacho": null,
  "fecha_despacho": null,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-23T10:00:00Z"
}
```

### Registro detalles_reposicion.csv

```json
{
  "id_detalle_reposicion": "DOR-001",
  "id_orden_reposicion": "ORD-001",
  "id_producto": "PRO-001",
  "cantidad_solicitada": 100,
  "costo_unitario": 3,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-20T09:00:00Z"
}
```

### Registro detalles_recepcion.csv

```json
{
  "id_detalle_recepcion": "DRE-001",
  "id_recepcion": "REC-001",
  "id_detalle_reposicion": "DOR-001",
  "id_inventario": "INV-001",
  "cantidad_recibida": 100,
  "cantidad_rechazada": 0,
  "cantidad_aceptada": 100,
  "lote": "DEMO-20251223",
  "fecha_vencimiento": "2026-12-23T00:00:00Z",
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": null,
  "motivo_rechazo": null,
  "id_movimiento": "MOV-ENT-001",
  "ubicado": true,
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

### Registro recepciones.csv

```json
{
  "id_recepcion": "REC-001",
  "id_orden_reposicion": "ORD-001",
  "id_operario": "OPE-001",
  "fecha_recepcion": "2025-12-23T10:00:00Z",
  "observaciones_generales": null,
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

## Archivos complementarios y auditoria

Tipos date/datetime segun convencion comun; todas las FKs apuntan a archivos base y mantienen empresa. simulado siempre true en extensiones. Todo int de ventas/cantidades/stock>=0 excepto delta_ajustes. No hay columnas adicionales tacitas.

### ventas_diarias.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197280. PK: fecha+id_almacen+id_producto. Regla/consumidor: Fuente para evaluacion nueva; ningun consumidor backend CSV. Ventas=sum SALIDA/VENTA; latente>=ventas; perdidas=latente-ventas; stockout=perdidas>0.

```csv
fecha,id_empresa,id_almacen,id_producto,id_inventario,ventas_observadas,demanda_latente,ventas_perdidas,stockout,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_empresa | str | No |
| id_almacen | str | No |
| id_producto | str | No |
| id_inventario | str | No |
| ventas_observadas | int | No |
| demanda_latente | int | No |
| ventas_perdidas | int | No |
| stockout | bool | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "id_inventario": "INV-001",
  "ventas_observadas": 10,
  "demanda_latente": 12,
  "ventas_perdidas": 2,
  "stockout": true,
  "simulado": true
}
```

### inventario_diario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197280. PK: fecha+id_inventario. Regla/consumidor: Auditoria replay: final=inicial+entradas-venta-otras+delta_ajustes. delta_ajustes puede ser firmado; stock/cantidades no negativos. Delta se calcula nuevo-anterior de AJUSTE absoluto.

```csv
fecha,id_inventario,stock_inicial,entradas,salidas_venta,salidas_otras,delta_ajustes,stock_final,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_inventario | str | No |
| stock_inicial | int | No |
| entradas | int | No |
| salidas_venta | int | No |
| salidas_otras | int | No |
| delta_ajustes | int | No |
| stock_final | int | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_inventario": "INV-001",
  "stock_inicial": 110,
  "entradas": 0,
  "salidas_venta": 10,
  "salidas_otras": 0,
  "delta_ajustes": 0,
  "stock_final": 100,
  "simulado": true
}
```

### saldos_iniciales.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario. Regla/consumidor: Apertura antes de primer movimiento, no ENTRADA ficticia ni snapshot de cierre. Stock>=0.

```csv
fecha_hora,id_inventario,stock_inicial,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha_hora | datetime | No |
| id_inventario | str | No |
| stock_inicial | int | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha_hora": "2020-01-01T00:00:00Z",
  "id_inventario": "INV-001",
  "stock_inicial": 110,
  "simulado": true
}
```

### calendario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 2199. PK: fecha. Regla/consumidor: 2020-01-01..2026-01-07. dayofweek lunes=0; semana ISO. Year ano calendario, aunque semana ISO pertenezca a otro ano. month1..12/day1..31/week1..53/quarter1..4/dayofyear1..366. Flags0/1. event_name {NINGUNO,FIN_ANIO,VERANO,INVIERNO}, event_type {NINGUNO,CAMPANIA}; has_event=algun nombre distinto de NINGUNO. snap=0. Calendario/campanas prepublicados antes del uso; conocido_en=2019-12-01.

```csv
fecha,year,month,day,dayofweek,weekofyear,quarter,dayofyear,is_weekend,is_month_start,is_month_end,has_event,event_name_1,event_type_1,event_name_2,event_type_2,snap,conocido_en,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| year | int | No |
| month | int | No |
| day | int | No |
| dayofweek | int | No |
| weekofyear | int | No |
| quarter | int | No |
| dayofyear | int | No |
| is_weekend | int | No |
| is_month_start | int | No |
| is_month_end | int | No |
| has_event | int | No |
| event_name_1 | str | No |
| event_type_1 | str | No |
| event_name_2 | str | No |
| event_type_2 | str | No |
| snap | int | No |
| conocido_en | datetime | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "year": 2025,
  "month": 12,
  "day": 31,
  "dayofweek": 2,
  "weekofyear": 1,
  "quarter": 4,
  "dayofyear": 365,
  "is_weekend": 0,
  "is_month_start": 0,
  "is_month_end": 1,
  "has_event": 1,
  "event_name_1": "FIN_ANIO",
  "event_type_1": "CAMPANIA",
  "event_name_2": "NINGUNO",
  "event_type_2": "NINGUNO",
  "snap": 0,
  "conocido_en": "2019-12-01T00:00:00Z",
  "simulado": true
}
```

### precios.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197910. PK: fecha+id_almacen+id_producto. Regla/consumidor: 2199 fechas*90 series. Precio>0, 2 decimales; moneda PEN. Plan mensual publicado primer dia a 00:00 UTC, antes del origen que lo usa. price_available siempre true en base; null de precio no admitido. No es costo compra. Precios enero 2026 se prepublican 2025-12-31 para horizonte al corte; no asumir conocidos antes de publicacion.

```csv
fecha,id_almacen,id_producto,sell_price,moneda,price_available,conocido_en,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_almacen | str | No |
| id_producto | str | No |
| sell_price | float | No |
| moneda | str | No |
| price_available | bool | No |
| conocido_en | datetime | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "sell_price": 4.5,
  "moneda": "PEN",
  "price_available": true,
  "conocido_en": "2025-12-01T00:00:00Z",
  "simulado": true
}
```

### series_mapping.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario; producto+almacen unico. Regla/consumidor: Adaptador futuro: item por SKU, dept=familia normalizada, cat=ALIMENTOS, store DEMO_LIMA/DEMO_AREQUIPA/DEMO_TRUJILLO, state LIMA/AREQUIPA/LA_LIBERTAD. IDs FK verificadas por rack/zona. Codigos semanticos nuevos, no vocabulario M5 garantizado.

```csv
id_inventario,id_empresa,id_almacen,id_producto,item_id,dept_id,cat_id,store_id,state_id,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| id_empresa | str | No |
| id_almacen | str | No |
| id_producto | str | No |
| item_id | str | No |
| dept_id | str | No |
| cat_id | str | No |
| store_id | str | No |
| state_id | str | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "item_id": "SKU_001",
  "dept_id": "CEREALES",
  "cat_id": "ALIMENTOS",
  "store_id": "DEMO_LIMA",
  "state_id": "LIMA",
  "simulado": true
}
```

### escenarios_inventario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario. Regla/consumidor: escenario {NORMAL,BAJO_STOCK,SIN_STOCK,SOBRESTOCK,SIN_CONSUMO,REFRIGERADO}; politica {NORMAL,REPOSICION_RETRASADA,COBERTURA_ALTA,INTERMITENTE}; explicacion no vacia, derivada de ledger. Etiquetas de simulacion, no enums backend.

```csv
id_inventario,fecha_corte,escenario,politica,explicacion,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| fecha_corte | date | No |
| escenario | str | No |
| politica | str | No |
| explicacion | str | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "fecha_corte": "2025-12-31",
  "escenario": "BAJO_STOCK",
  "politica": "REPOSICION_RETRASADA",
  "explicacion": "Stock bajo tras retraso de entrega y ventas recientes",
  "simulado": true
}
```

### inventario_historial.csv

Estado: coleccion existente, exportacion nueva. Registros: 90 minimo. PK: id_inventario+fecha+accion. Regla/consumidor: Coleccion existente; InventarioRepository e InventarioHistorialResponse (proyeccion sin id_inventario). CREAR por inventario, EDITAR_LIMITES solo si se simulan; antes/despues snapshots de campos afectados, no espejo de movimientos.

```csv
id_inventario,id_operario,accion,antes,despues,fecha
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| id_operario | str | Si |
| accion | str | No |
| antes | dict | Si |
| despues | dict | Si |
| fecha | datetime | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "id_operario": null,
  "accion": "CREAR",
  "antes": null,
  "despues": {
    "id_producto": "PRO-001",
    "id_rack": "RAC-001",
    "stock_actual": 110,
    "stock_minimo": 40,
    "stock_maximo": 500
  },
  "fecha": "2019-12-06T00:00:00Z"
}
```

## Reglas particulares de archivos base

- empresas: una empresa ficticia, RUC string sintetico (no validar existencia SUNAT); correo example.com, correo_verificado=false/fecha_verificacion=null. Fechas ISO strings. Sin password.
- almacenes: nombres/ubicaciones ficticios, coordenadas hasta 6 decimales en rangos DTO, area1200/aforo25/tipo_almacen Mixto (valor elegido, no enum).
- zonas: seca/refrigerada por almacen; nombre/tipo_zona strings Seco/Refrigerado elegidos, capacidad5; flag refrigerada coherente. Rangos null seca, 2..6 refrigerada.
- racks: 5 niveles por zona, codigo unico por zona, 5000kg de diseno; estado DISPONIBLE base. No deducir LLENO de stock arbitrariamente; estado es dato operativo, carga/libre se calculan al consultar.
- proveedores: 3 activos, lead2/4/7; RUC11 caracteres unico, correos null o example.com, flags cuenta=false sin credential.
- productos: 15 secos/15 refrigerados, nombres alimenticios, peso kg>0, volumen null, lead del proveedor, vida_util>=1; categoria/familia/marca elegidas sin catalogo backend. id_rack referencia a una ubicacion principal (por ejemplo Lima), no sustituye otros inventarios. Restriccion de agregados legacy advertida.
- operarios: 2 por almacen, ACTIVO, cargo Almacenero, turnos Manana/Tarde como valores de demo; correo example.com unico; sin credential/tiene_cuenta=false.
- inventario: 90 cierres; min/max politica fija, stock resultante de replay. No copiar stock de Producto.
- ordenes/detalles/recepciones: una linea por orden y una recepcion conforme cuando entregada, MANUAL, sin recomendacion; suma aceptada determina estado. Conteos estimados dependen de politica/ruido, no cuota forzada. No generar recepciones posteriores al corte. Campos despacho/comentario se dejan null base si no se simulan.
- detalles_recepcion: lote sintetico, vencimiento coherente con vida util, temperatura dentro de rango si refrigerado; estado CONFORME, rechazadas0/aceptadas=recibidas, ubicado=true, FK a entrada. Riesgo/notificacion son resultados omitidos, reconstruir null al validar Response.
- movimientos: ventas diarias positivas agregadas + entradas aceptadas; aproximadamente hasta197280 SALIDA mas20k..40k entradas; menos filas si ventas0. El numero no es criterio de aceptacion fijo. Otras salidas/ajustes0 base. No IDs ficticios de pedido cliente.

## Auxiliares obligatorios

manifest.json (1 registro): schema_version str=1.0; dataset_id str; simulated bool=true; seed int=20261010; generator_version str; source_contract_sha256 objeto archivo -> hash; parameters objeto configuracion exacta; history_start/history_end/reference_date date (2020-01-01/2025-12-31/2025-12-31); timezone str=UTC; id_namespace str UUID; splits objeto TRAIN/VALID/TEST -> {target_start:date,target_end:date}; files lista {path:str,rows:int,sha256:str}; exclusions lista str; limitations lista str. No hash autorreferente del manifest.

validation_report.json (1): schema_version str, dataset_id str, passed bool, checks lista {name:str,passed:bool,failures:int,examples:list}, counts objeto, warnings lista str. schema.json: archivosi{columns:lista {name:str,type:str,nullable:bool,allowed_values:list|null},primary_key:lista str,foreign_keys:lista {columns:list,target_file:str,target_columns:list}}. README_GENERATOR.md: comandos, seed/versiones/config, mediciones reales y limites. No credenciales en ejemplos.

Ejemplo minimo de manifest (completar listas/huellas al generar):

```json
{"schema_version":"1.0","dataset_id":"psitwin-demo-v1","simulated":true,"seed":20261010,"generator_version":"1.0.0","source_contract_sha256":{},"parameters":{},"history_start":"2020-01-01","history_end":"2025-12-31","reference_date":"2025-12-31","timezone":"UTC","id_namespace":"a1d188f7-265c-5ebc-894a-b65ea36c236f","splits":{"TRAIN":{"target_start":"2020-01-01","target_end":"2023-12-31"},"VALID":{"target_start":"2024-01-01","target_end":"2024-12-31"},"TEST":{"target_start":"2025-01-01","target_end":"2025-12-31"}},"files":[],"exclusions":["credenciales","predicciones"],"limitations":["Sin importador CSV actual"]}
```

Exportaciones mongo/*.jsonl para13 entidades base+inventario_historial: mismas columnas persistentes de CSV, datetime transformados a Extended JSON {"$date":"..."}, excepto strings fecha de empresa; Decimal coordenadas se persiste float finito con6 decimales. Sin _id/credenciales. Recepciones no guardan lista detalles en cabecera: unir detalles al construir Response. No cargar automaticamente.

## Excluidos

No pedidos.csv: no existe pedido cliente. No alertas.csv/recomendaciones.csv/forecast precalculado: son resultados del backend, sus contratos estan documentados. No cuentas/secretos/email_verifications/notificaciones_email. No matriz features/pickle entrenable obligatoria: fuentes completas bastan para posterior ML. Si una futura exposicion exige pedidos comerciales o FEFO persistente, definir extension de cabeceras/lineas/lotes previamente y versionar contrato.

### Ejemplos de auxiliares de validacion/esquema

Ejemplo ilustrativo de validation_report.json (checks reales deben cubrir todo VALIDATION_CHECKLIST):

```json
{"schema_version":"1.0","dataset_id":"psitwin-demo-v1","passed":true,"checks":[{"name":"referencias","passed":true,"failures":0,"examples":[]}],"counts":{"empresas":1},"warnings":["Sin importador CSV actual"]}
```

Ejemplo parcial de schema.json (completar todos archivos/columnas al generar):

```json
{"saldos_iniciales.csv":{"columns":[{"name":"fecha_hora","type":"datetime","nullable":false,"allowed_values":null},{"name":"id_inventario","type":"str","nullable":false,"allowed_values":null},{"name":"stock_inicial","type":"int","nullable":false,"allowed_values":null},{"name":"simulado","type":"bool","nullable":false,"allowed_values":[true]}],"primary_key":["id_inventario"],"foreign_keys":[{"columns":["id_inventario"],"target_file":"inventario.csv","target_columns":["id_inventario"]}]}}
```


---

# DOCUMENTO INCLUIDO: VALIDATION_CHECKLIST.md

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
