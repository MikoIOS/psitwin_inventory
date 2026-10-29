"""Prevent credentials in query strings from reaching application-server logs."""
import logging
import re


class AuthQueryFilter(logging.Filter):
    def filter(self, record):
        def redact(value):
            return re.sub(r'(?i)([?&](?:token|code|state)=)[^\s"&]+', r'\1[REDACTED]', value) if isinstance(value, str) else value
        record.msg = redact(record.msg)
        # Uvicorn's access formatter also reads the five structured arguments.
        if isinstance(record.args, tuple):
            record.args = tuple(redact(value) for value in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: redact(value) for key, value in record.args.items()}
        return True


def install_auth_log_redaction():
    for name in ('uvicorn.access', 'uvicorn.error'):
        logger = logging.getLogger(name)
        if not any(isinstance(item, AuthQueryFilter) for item in logger.filters):
            logger.addFilter(AuthQueryFilter())
