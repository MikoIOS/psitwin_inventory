import asyncio
from unittest.mock import AsyncMock, Mock
import pytest
from app.dto.saiki_dto import SaikiAskRequest
from app.services.saiki_input import intelligible_input
from app.services.saiki_service import SaikiService


@pytest.mark.parametrize('text', ['...', '!!', 'eh eh mmm', 'qwerty', 'silencio', '12345'])
def test_noise_never_reaches_model(text, monkeypatch):
    service = SaikiService()
    agent = AsyncMock(side_effect=AssertionError('No llamar al LLM'))
    monkeypatch.setattr(service, '_agent_loop', agent)
    result = asyncio.run(service.ask(SaikiAskRequest(message=text)))
    assert result['answer'] == '' and result['data']['ignorado']
    agent.assert_not_awaited()


@pytest.mark.parametrize('text', ['Hola', 'Sí', '¿Y mañana?', '¿Puedes explicarme la rotación?', '¿Qué provoca ese ruido?', 'Revisa SKU ABC-123'])
def test_unknown_legitimate_questions_are_not_dropped(text):
    assert intelligible_input(text)
