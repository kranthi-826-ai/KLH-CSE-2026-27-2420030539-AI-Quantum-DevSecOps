"""Validated SMTP configuration; secrets never appear in the rendered Alertmanager document."""
from pathlib import Path
import re

KEYS = {'SMTP_HOST', 'SMTP_PORT', 'SMTP_FROM', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'ALERT_EMAIL_TO'}
ADDRESS = re.compile(r'[A-Za-z0-9.!%+_\-]+@[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?\Z')


def parse_settings(text):
    settings = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or key not in KEYS or key in settings:
            raise ValueError('Email configuration has unknown, malformed or duplicate fields')
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        settings[key] = value
    if set(settings) != KEYS or any(not value for value in settings.values()):
        raise ValueError('All required email configuration fields must be supplied')
    if any('\r' in value or '\n' in value or '\x00' in value for value in settings.values()):
        raise ValueError('Email configuration contains unsupported control characters')
    host = settings['SMTP_HOST']
    if len(host) > 253 or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?', host):
        raise ValueError('SMTP host is invalid')
    try:
        port = int(settings['SMTP_PORT'])
    except ValueError:
        raise ValueError('SMTP port is invalid') from None
    if not 1 <= port <= 65535:
        raise ValueError('SMTP port is invalid')
    for key in ('SMTP_FROM', 'ALERT_EMAIL_TO'):
        if len(settings[key]) > 254 or not ADDRESS.fullmatch(settings[key]):
            raise ValueError('A sender or recipient address is invalid')
    if len(settings['SMTP_USERNAME']) > 254 or len(settings['SMTP_PASSWORD']) > 1024:
        raise ValueError('SMTP authentication settings exceed supported limits')
    return settings


def alertmanager_document(settings, password_file):
    # Validate even callers which bypass the dotenv parser. No input becomes a template.
    settings = parse_settings('\n'.join(f'{key}={value}' for key, value in settings.items()))
    return {
        'global': {'smtp_smarthost': settings['SMTP_HOST'] + ':' + settings['SMTP_PORT'],
                   'smtp_from': settings['SMTP_FROM'], 'smtp_auth_username': settings['SMTP_USERNAME'],
                   'smtp_auth_password_file': str(password_file), 'smtp_require_tls': True,
                   'smtp_force_implicit_tls': int(settings['SMTP_PORT']) == 465},
        'route': {'receiver': 'operator-email', 'group_by': ['alertname', 'application', 'instance'],
                  'group_wait': '30s', 'group_interval': '5m', 'repeat_interval': '4h'},
        'receivers': [{'name': 'operator-email', 'email_configs': [{
            'to': settings['ALERT_EMAIL_TO'], 'send_resolved': True,
            'headers': {'Subject': 'AI-PQC {{ .Status }} · {{ .GroupLabels.alertname }}'},
            'text': 'AI-PQC audit delivery: {{ .Status }}\n{{ range .Alerts }}Rule: {{ .Labels.alertname }}\nProducer: {{ .Labels.application }}\nTarget: {{ .Labels.instance }}\n{{ .Annotations.summary }}\n{{ .Annotations.description }}\n{{ end }}',
            'html': ''}]}]}


def prometheus_email_config(base_text):
    # Extend the controlled tracked base without reserializing or changing scrape/rule settings.
    if re.search(r'^alerting\s*:', base_text, re.MULTILINE):
        raise ValueError('Base Prometheus configuration already declares alert delivery; review instead of duplicating it')
    return base_text.rstrip() + '\n\nalerting:\n  alertmanagers:\n    - static_configs:\n        - targets: ["alertmanager:9093"]\n'
