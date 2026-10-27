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
