"""Per-request progress, isolated across tenants and concurrent conversations."""
from contextvars import ContextVar

sink = ContextVar('saiki_progress_sink', default=None)

def report(phase, detail='', *, long=False, timeout_ms=None):
    callback = sink.get()
    if callback:
        event = {'type': 'progress', 'phase': phase, 'detail': detail, 'long': long}
        if timeout_ms is not None: event['timeout_ms'] = timeout_ms
        callback(event)
