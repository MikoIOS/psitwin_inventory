"""Shared SMTP transport: implicit TLS on 465, STARTTLS on other configured ports."""
import smtplib
import ssl
from app.config.settings import settings


class DeliveryUncertain(RuntimeError):
    """SMTP may have accepted DATA. Retrying automatically could deliver twice."""


def send_message(message, host=None, port=None, user=None, password=None):
    host, port = host or settings.smtp_host, port or settings.smtp_port
    user, password = user or settings.smtp_user, password or settings.smtp_secret
    # Gmail displays application passwords in groups; pasted whitespace is not
    # part of the password (including non-breaking spaces from the browser).
    if host.lower() == 'smtp.gmail.com' and password:
        password = ''.join(password.split())
    context = ssl.create_default_context()
    connection = (smtplib.SMTP_SSL(host, port, timeout=20, context=context) if port == 465
                  else smtplib.SMTP(host, port, timeout=20))
    server = connection
    try:
        if port != 465:
            if not settings.smtp_use_tls: raise ValueError('SMTP requiere TLS')
            server.starttls(context=context)
        server.login(user, password)
        try:
            refused = server.send_message(message)
            if refused: raise smtplib.SMTPRecipientsRefused(refused)
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPDataError):
            raise
        except Exception as error:
            raise DeliveryUncertain('Confirmación de entrega desconocida') from error
    finally:
        # DATA acceptance is the delivery result; a failing QUIT must not turn it into a retry.
        try: server.close()
        except Exception: pass
