"""Send one clearly labelled welcome test to the configured sender itself.

Never prints secrets and never creates or modifies a company.
"""
import json
import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config.settings import settings
from app.services.smtp_transport import send_message, DeliveryUncertain
from app.services.welcome_email_service import build_welcome_message

report = {
    'email_enabled': settings.email_enabled,
    'host_gmail': settings.smtp_host == 'smtp.gmail.com',
    'port': settings.smtp_port,
    'sender_expected': settings.smtp_user == 'psitwin2026@gmail.com',
    'password_configured': bool(settings.smtp_secret),
    'smtp_accepted': False,
    'inbox_receipt_verified': False,
}
if all(report[k] for k in ('email_enabled', 'host_gmail', 'sender_expected', 'password_configured')):
    try:
        message = build_welcome_message({'nombre_ceo': 'Prueba de correo',
            'correo': settings.smtp_user, 'id_empresa': 'smtp-test-' + uuid4().hex})
        message.replace_header('Subject', 'Prueba técnica — bienvenida PsiTwin')
        send_message(message)
        report['smtp_accepted'] = True
    except Exception as error:
        report['error_type'] = type(error).__name__
        report['delivery_uncertain'] = isinstance(error, DeliveryUncertain)
else:
    report['pending'] = 'Completa SMTP y habilita EMAIL_ENABLED; no se intentó el envío.'
print(json.dumps(report, ensure_ascii=True, indent=2))
sys.exit(0 if report['smtp_accepted'] else 1)
