import asyncio
from types import SimpleNamespace

import pytest

from app.services.saiki_grounding import grounded_answer, public_evidence
from app.services.saiki_service import SaikiService, OllamaUnavailableError


def test_diagnostics_are_private_but_stock_and_demand_are_preserved():
    result = public_evidence({'modelo': 'WeightedEnsemble', 'runtime': {'version': '1.6.1'},
                              'filas': [{'stock_actual': 0, 'demanda_acumulada': 21}],
                              'evaluacion': {'7': 18.27}})
    assert result == {'filas': [{'stock_actual': 0, 'demanda_acumulada': 21}]}


@pytest.mark.parametrize('candidate', [
    'La demanda será de 999 unidades.',
    'El stock es 21 y la demanda es 4.',
    'AutoGluon predice 21 unidades.',
    'El sensor falló y habrá desabastecimiento.',
    'La demanda es cero.',
])
def test_interpretation_rejects_invented_numbers_changed_roles_and_causes(candidate):
    assert not grounded_answer(candidate, 'La demanda es 21. El stock es 4.')


def test_interpretation_accepts_only_verified_statements():
    assert grounded_answer('El stock es 4. La demanda es 21.', 'La demanda es 21. El stock es 4.')


def test_agent_cannot_skip_predictive_tools_and_invent_demand(monkeypatch):
    service = SaikiService()
    monkeypatch.setattr(service, '_call_ollama_chat', lambda *args: {
        'message': {'content': 'La demanda será 999 unidades.'}})
    answer, evidence, sources = asyncio.run(service._agent_loop([], None, frozenset({'get_forecast'})))
    assert '999' not in answer
    assert 'No hay resultados' in answer
    assert not evidence and not sources


@pytest.mark.parametrize('mode', ['verified', 'invented', 'offline'])
def test_llm_receives_real_evidence_and_cannot_replace_forecast(monkeypatch, mode):
    service = SaikiService()
    verified = 'La demanda es 21. El stock es 4.'
    calls = []

    def llm(messages, names):
        calls.append(messages)
        assert not names
        assert 'WeightedEnsemble' not in messages[-1]['content']
        if mode == 'offline':
            raise OllamaUnavailableError('offline')
        return {'message': {'content': verified if mode == 'verified' else 'La demanda es 999.'}}

    monkeypatch.setattr(service, '_call_ollama_chat', llm)
    result = asyncio.run(service._interpret_demand('Explica la demanda', verified, {},
        {'get_forecast': {'demanda_total_estimada': 21, 'modelo': 'WeightedEnsemble'}}, {'AUTOGLUON'}))
    assert len(calls) == 1
    assert result['answer'] == verified
    assert 'modelo' not in result['data']['get_forecast']
    assert result['source'] == ('ollama' if mode == 'verified' else 'backend')
