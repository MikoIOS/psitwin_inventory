from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class SaikiIntent:
    kind: str
    tool_names: frozenset[str]
    horizon_days: int | None = None
    needs_horizon: bool = False


class SaikiIntentRouter:
    """Route clear requests; leave uncertain requests to the model."""
    SUPPORTED_HORIZONS = frozenset({1, 7, 30, 90})
    CURRENT_TOOLS = frozenset({'get_warehouse_status', 'get_inventory', 'get_product', 'get_active_alerts', 'get_recommendations', 'get_recent_movements'})
    PREDICTIVE_TOOLS = frozenset({'get_warehouse_status', 'get_inventory', 'get_product', 'get_forecast', 'get_inventory_risk'})
    MIXED_TOOLS = CURRENT_TOOLS | PREDICTIVE_TOOLS

    @staticmethod
    def _normalize(text):
        return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))

    @classmethod
    def classify(cls, message: str, history: list[dict] | None = None) -> SaikiIntent:
        text = cls._normalize(message)
        plain = re.sub(r'[^a-z0-9\s]', '', text).strip()
        if 'explora tus sensores' in text:
            return SaikiIntent('platform_help', frozenset())
        if re.search(r'microfono|voz de saiki|conversacion por voz|transcripcion|reconocimiento|freetts|\bjorge\b', text):
            return SaikiIntent('platform_help', frozenset())
        if re.search(r'ofert|proveedor|distribuidor|solicitud|pedido|despacho|recepcion|rechaz|faltante|costarian|cuanto cuesta|cada cuantos dias.*pedido|kilos?.*solicitar|frecuencia.*reposicion|grafico.*demanda', text):
            return SaikiIntent('abastecimiento', frozenset())
        if re.search(r'quien eres|quien es saiki|que puedes hacer|como me ayudas|como puedes ayudar|que haces|presentate', text):
            return SaikiIntent('identity', frozenset())
        if re.fullmatch(r'(muchas )?gracias( saiki)?|adios( saiki)?|hasta luego|nos vemos', plain):
            return SaikiIntent('courtesy', frozenset())
        if re.search(r'como\s+(?:creo|registro|agrego|veo|consulto|interpreto)\b', text):
            return SaikiIntent('platform_help', frozenset())
        if re.search(r'como (?:puedo |se |hago para |podria )?(?:crear|registrar|agregar|anadir|editar|eliminar|ver|consultar|administrar|gestionar|usar|utilizar|configurar|vincular)|pasos para|donde (?:creo|registro|agrego)|como funciona|ayuda (?:con|para)|funciones de psitwin|limitaciones de psitwin', text):
            return SaikiIntent('platform_help', frozenset())
        if cls._general_advice(text):
            return SaikiIntent('conversation', frozenset())
        if cls._example_followup(plain):
            for item in reversed((history or [])[-8:]):
                if item.get('role') != 'user':
                    continue
                previous = cls._normalize(str(item.get('content', '')))
                previous_plain = re.sub(r'[^a-z0-9\s]', '', previous).strip()
                if cls._example_followup(previous_plain):
                    continue
                if cls.classify(previous).kind == 'conversation':
                    return SaikiIntent('conversation', frozenset())
                break
        if re.search(r'operario|empleado|personal', text):
            return SaikiIntent('workforce', frozenset({'get_workforce'}))
        if re.search(r'disponibilidad|analiza (?:este registro|la informacion disponible)', text):
            return SaikiIntent('operational_analysis', cls.CURRENT_TOOLS)
        if re.search(r'\b(?:cuantos?|numero|lista|muestra|tengo|hay)\b.*\b(?:almacen|almacenes|zonas?|racks?)\b|\b(?:almacenes|zonas|racks)\b.*\b(?:tengo|hay)\b', text) and not re.search('sensor|temperatura|humedad|alerta', text):
            return SaikiIntent('locations', frozenset({'get_locations'}))
        if re.search(r'sensor|temperatura|humedad|refrigera|equipo de frio|corriente|incidente|calibr|mantenimiento|puerta|alertas?.*(?:mes|semana)|madrugada', text):
            return SaikiIntent('sensors', frozenset())
        if (re.search(r'demanda|tendencia', text)
                and not re.search(r'futur|proyect|pronostic|predic|autogluon|manana|proxim|esperad|reabastec|recomend|accion|stock|existencia', text)
                and (cls._horizon_days(text) is None or re.search(r'histor|pasad|ultim|observad', text))):
            return SaikiIntent('historical_demand', frozenset({'get_historical_demand'}))
        if re.search(r'autogluon|weightedensemble|wape|confiab|fiable|mayor demanda|mas demanda|demanda proyectada|reabastec|espera vender|(?:accion|recomend).*demanda|demanda.*(?:stock|existencia)', text):
            return SaikiIntent('demand_analysis', frozenset({'get_demand_analysis'}), cls._horizon_days(text) or 30)
        if re.fullmatch(r'\s*(hola|buenos dias|buenas tardes|buenas noches|hey)(\s+saiki)?[!,.?\s]*', plain):
            return SaikiIntent('greeting', frozenset())
        horizon = cls._horizon_days(text)
        analysis = bool(re.search(r'analiz|evalua|prioriz|justific|por que|motivo|explica', text))
        replenishment = bool(re.search(r'repon|reposicion|comprar|recomend', text))
        if analysis and replenishment:
            return SaikiIntent('analysis', cls.MIXED_TOOLS, horizon)
        listing = bool(re.search(r'mencion|enumera|lista|listado|detalle|desglos|muestra|dime|dame|ensena|quiero ver|que productos', text))
        inventory = bool(re.search(r'producto|inventario|existencia|stock', text))
        location = bool(re.search(r'ubicacion|rack|zona|donde', text))
        quantities = bool(re.search(r'cantidad|stock|unidades|existencia', text))
        other_operation = bool(re.search(r'alert|movimiento|entrada|salida|riesgo|agot|demanda|predic|repon|recomend', text))
        if listing and inventory and not other_operation:
            if location:
                return SaikiIntent('inventory_detail', frozenset({'get_warehouse_status'}))
            if quantities or re.search(r'mencion|enumera|listado|lista\b|todos.*productos', text):
                return SaikiIntent('product_quantities', frozenset({'get_warehouse_status', 'get_product'}))
        predictive = bool(re.search(r'proyect|proyecc|pronostic|predec|predic|demanda futura|agot|quedarse sin|alcanzara|necesitare', text)) or (bool(re.search(r'demanda|vendera|venderan', text)) and horizon is not None)
        if predictive or (horizon is not None and cls._history_has_predictive_request(history)):
            return SaikiIntent('predictive', cls.PREDICTIVE_TOOLS, horizon if horizon is not None else 7)
        qualified = bool(re.search(r'\brack|\bzona|\bcon\b|\bsin\b|\b(?:de|en|para|del)\b', text))
        if not qualified and re.search(r'\bcuantos? productos\b', text) and re.search(r'\btengo\b', text):
            return SaikiIntent('product_count', frozenset({'get_product'}))
        if not qualified and re.search(r'\b(?:tengo|hay|existen) almacenes\b', text):
            return SaikiIntent('warehouses', frozenset({'get_warehouse_status'}))
        if not qualified and re.search(r'\bcuanto (?:stock|inventario)\b', text) and re.search(r'\btengo\b', text):
            return SaikiIntent('stock_total', frozenset({'get_warehouse_status'}))
        if not other_operation and not re.search(r'\b(?:dias?|semanas?|meses|precio|cost|tendre|necesitare)\b', text) and (re.search(r'\bcantidad\b|\bcuant[oa]s?\b.*\b(?:tengo|hay|queda|quedan|tenemos|disponible)', text)):
            return SaikiIntent('stock_quantity', frozenset({'get_warehouse_status'}))
        categories = [
            ('movements', r'movimiento|entrada|salida|venta|historial', {'get_recent_movements'}),
            ('alerts', r'alerta|aviso', {'get_active_alerts'}),
            ('recommendations', r'recomend|reponer|reposicion|comprar', {'get_recommendations'}),
            ('risk', r'riesgo|desabastec', {'get_inventory_risk', 'get_forecast', 'get_warehouse_status'}),
            ('location', r'donde|ubicacion|localiza|en que rack|en que zona', {'get_warehouse_status', 'get_product'}),
            ('stock', r'stock|existencia|cuantas unidades|cantidad disponible', {'get_warehouse_status', 'get_inventory', 'get_product'}),
            ('products', r'producto|catalogo', {'get_product', 'get_warehouse_status'}),
        ]
        matches = [(kind, tools) for kind, pattern, tools in categories if re.search(r'\b(?:' + pattern + ')', text)]
        if matches:
            tools = frozenset().union(*(tools for _, tools in matches))
            return SaikiIntent(matches[0][0] if len(matches) == 1 else 'mixed', tools)
        if re.search(r'\bmuestrame\s+(?:el|la)\b', text):
            return SaikiIntent('products', frozenset({'get_product', 'get_warehouse_status'}))
        if re.search(r'inventario|almacen', text) and re.search(r'como|estado|resumen|situacion|panorama', text):
            return SaikiIntent('general', frozenset({'get_warehouse_status'}))
        if re.search(r'\b(?:explica|explicame|conversemos|opinas|significa|que es|que son|por que)\b', text):
            return SaikiIntent('conversation', frozenset())
        return SaikiIntent('ambiguous', frozenset())

    @staticmethod
    def _general_advice(text):
        # Advice about organizing a warehouse is not a request for its live stock.
        return bool(re.search(
            r'\b(?:como\s+(?:(?:puedo|podemos|se|debo)\s+)?|consejos?\s+para\s+|'
            r'buenas practicas\s+para\s+)(?:organizar|ordenar|distribuir|almacenar|conservar|clasificar)\b',
            text,
        ))

    @staticmethod
    def _example_followup(plain):
        return bool(re.fullmatch(
            r'(?:(?:puedes|podrias) )?(?:dame |darme |ponme |muestrame )?'
            r'(?:un |otro )?ejemplo(?: practico| concreto| sencillo)?(?: por favor)?', plain,
        ))

    @classmethod
    def _history_has_predictive_request(cls, history):
        return any(re.search(r'proyect|proyecc|pronostic|predic|agot|demanda futura', cls._normalize(str(item.get('content', '')))) for item in (history or [])[-4:] if item.get('role') == 'user')

    @staticmethod
    def _horizon_days(text):
        if re.search(r'\bmanana\b', text):
            return 1
        if re.search(r'\btres meses\b', text):
            return 90
        text = re.sub(r'\bnoventa\b', '90', text)
        text = re.sub(r'\btreinta\b', '30', text)
        text = re.sub(r'\bsiete\b', '7', text)
        match = re.search(r'\b(\d+)\s*(dias?|semanas?|mes(?:es)?)\b', text)
        if match:
            return int(match[1]) * (7 if 'semana' in match[2] else 30 if 'mes' in match[2] else 1)
        if re.search(r'\b(?:una|la proxima|esta) semana\b', text):
            return 7
        if re.search(r'\b(?:un|el proximo|este) mes\b', text):
            return 30
        return None
