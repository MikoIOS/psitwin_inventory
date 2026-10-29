"""Keep diagnostics private and reject unsupported numeric LLM interpretations."""
import re
from decimal import Decimal, InvalidOperation

PRIVATE_KEYS = {'modelo', 'model', 'motor', 'version', 'version_modelo', 'tipo_modelo',
                'runtime', 'evaluacion', 'model_fingerprint', 'features_por_horizonte'}
TECHNICAL = re.compile(r'autogluon|weightedensemble|qwen|ollama|reentrena|holdout|traceback', re.I)


def public_evidence(value):
    if isinstance(value, dict):
        return {key: public_evidence(item) for key, item in value.items() if key not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [public_evidence(item) for item in value]
    if isinstance(value, str) and TECHNICAL.search(value):
        return 'Información de diagnóstico disponible internamente.'
    return value


def numbers(text):
    result = set()
    for token in re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)?', text):
        try:
            result.add(Decimal(token.replace(',', '.')))
        except InvalidOperation:
            pass
    return result


def grounded_answer(candidate, verified):
    if not candidate or TECHNICAL.search(candidate):
        return False
    if not numbers(candidate).issubset(numbers(verified)):
        return False
    # Conservative semantic boundary: unverified causal/risk claims and changed facts
    # must never become operational advice merely because their numbers match.
    sentences = [part.strip() for part in re.split(r'(?<=[.!?])\s+|\n+', candidate) if part.strip()]
    approved = ' '.join(verified.split()).casefold()
    return bool(sentences) and all(' '.join(sentence.split()).casefold() in approved for sentence in sentences)
