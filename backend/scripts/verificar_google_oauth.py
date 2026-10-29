"""Check local OAuth configuration without printing credentials or calling Google."""
from pathlib import Path
import json
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config.settings import settings

callback = urlsplit(settings.google_redirect_uri)
origin = f'{callback.scheme}://{callback.netloc}'
report = {
    'client_id_configurado': bool(settings.google_client_id.strip()),
    'client_secret_configurado': bool(settings.google_client_secret.strip()),
    'redirect_uri': settings.google_redirect_uri,
    'frontend_url': settings.frontend_url,
    'origen_callback_permitido_cors': origin in settings.cors_origins_list,
    'ruta_callback_correcta': callback.path == '/auth/google/callback',
    'nota': 'Este chequeo no valida las credenciales contra Google ni sustituye el consentimiento real.',
}
print(json.dumps(report, ensure_ascii=True, indent=2))
sys.exit(0 if all(report[key] for key in ('client_id_configurado', 'client_secret_configurado', 'origen_callback_permitido_cors', 'ruta_callback_correcta')) else 1)
