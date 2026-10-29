"""Routing and evidence rendering; synthetic fixtures are never operational forecasts."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.saiki_intent_router import SaikiIntentRouter
from app.services import saiki_demand

def test_selected_warehouse_does_not_force_inventory_questions_into_demand(monkeypatch):
    from app.services.saiki_service import SaikiService
    from app.dto.saiki_dto import SaikiAskRequest
    from app.dto.auth_dto import UsuarioActual
    service = SaikiService()
    current = AsyncMock(return_value={'answer': 'Tienes 10 productos registrados.'})
    monkeypatch.setattr(service, '_fast_current_response', current)
    demand = AsyncMock(side_effect=AssertionError('Inventory count must not request forecasts'))
    monkeypatch.setattr(saiki_demand, 'demand_answer', demand)
    result = asyncio.run(service.ask(SaikiAskRequest(message='¿Cuántos productos tengo registrados?', id_almacen='selected'), UsuarioActual(rol='EMPRESA', id_empresa='test')))
    assert '10' in result['answer']
    current.assert_awaited_once()
    demand.assert_not_awaited()


@pytest.mark.parametrize('question,horizon', [
    ('Que productos tendran mayor demanda durante los proximos 30 dias?', 30),
    ('Cuanto se espera vender de este producto?', 30),
    ('Que almacenes podrian necesitar reabastecimiento?', 30),
    ('Que tan confiable es esta prediccion?', 30),
    ('Que acciones se recomiendan segun la demanda y el stock disponible?', 30),
    ('AutoGluon para los proximos 90 dias', 90),
])
def test_analysis_questions(question, horizon):
    intent = SaikiIntentRouter.classify(question, [])
    assert intent.kind == 'demand_analysis'
    assert intent.horizon_days == horizon


def test_missing_predictions_never_become_invented_demand(monkeypatch):
    summary = {'filas': [], 'calculando': False, 'completo': True}
    service = SimpleNamespace(summary=AsyncMock(return_value=summary), metadata=lambda: {
        'wape_accumulated_pct': {'1': 37.43, '7': 18.27, '30': 15.25, '90': 14.98},
        'runtime': {'validado': False, 'faltantes': ['missing weights']},
    })
    monkeypatch.setattr(saiki_demand, 'service', service)
    answer, evidence = asyncio.run(saiki_demand.demand_answer(SimpleNamespace(id_empresa='owned')))
    assert 'No hay pronósticos válidos' in answer
    assert 'missing weights' not in answer
    assert 'no está disponible' in answer
    assert 'missing weights' in evidence['runtime']['faltantes']
    assert evidence['filas'] == []
    assert evidence['tipo_modelo'] == 'EVALUACION_NO_REENTRENADO'
