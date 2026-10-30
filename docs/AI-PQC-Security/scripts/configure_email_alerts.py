"""Validate root .env.email; optional --apply writes only ignored runtime SMTP files."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from email_alert_config import parse_settings, alertmanager_document, prometheus_email_config

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    settings_file = ROOT / '.env.email'
    if not settings_file.is_file():
        raise ValueError('Create Git-ignored .env.email from infrastructure/monitoring/email.env.example first')
    settings = parse_settings(settings_file.read_text(encoding='utf-8-sig'))
    if not args.apply:
        print('Email configuration validates. Nothing written, connected or sent. Use --apply to prepare ignored runtime files.')
        return
    for directory in (ROOT / '.runtime', ROOT / '.runtime/email'):
        if directory.is_symlink() or directory.is_junction():
            raise ValueError('Runtime output must not pass through linked directories')
        directory.mkdir(exist_ok=True)
    directory = ROOT / '.runtime/email'
    outputs = [directory / name for name in ('smtp-password', 'alertmanager.yml', 'prometheus.yml')]
    if any(path.is_symlink() or path.is_junction() for path in outputs):
        raise ValueError('Runtime outputs must not be linked paths')
    base = (ROOT / 'infrastructure/monitoring/prometheus.yml').read_text(encoding='utf-8')
    prometheus_text = prometheus_email_config(base)
    config_text = json.dumps(alertmanager_document(settings,'/etc/alertmanager/secrets/smtp-password'),indent=2)
    if os.name == 'nt':
        # Restrict this task-owned directory before writing credentials; no global ACL changes.
        result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
            "$p=[Environment]::GetEnvironmentVariable('PQC_EMAIL_OUTPUT_DIRECTORY'); $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User; $acl=[Security.AccessControl.DirectorySecurity]::new(); $acl.SetAccessRuleProtection($true,$false); $acl.SetOwner($sid); $rule=[Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'); $acl.AddAccessRule($rule); Set-Acl -LiteralPath $p -AclObject $acl"],
            env={**os.environ,'PQC_EMAIL_OUTPUT_DIRECTORY':str(directory)}, capture_output=True, timeout=15)
        if result.returncode:
            raise ValueError('Could not restrict runtime email directory permissions; no SMTP secret was written')
    else:
        directory.chmod(0o700)
    password = directory / 'smtp-password'
    if password.is_symlink() or password.is_junction():
        raise ValueError('SMTP password output must not be a linked path')
    password.write_text(settings['SMTP_PASSWORD'], encoding='utf-8')
    password.chmod(0o600)
    config = directory / 'alertmanager.yml'
    if config.is_symlink() or config.is_junction():
        raise ValueError('Runtime config output must not be a linked path')
    config.write_text(config_text,encoding='utf-8')
    config.chmod(0o600)
    prometheus = directory / 'prometheus.yml'
    if prometheus.is_symlink() or prometheus.is_junction():
        raise ValueError('Prometheus runtime output must not be a linked path')
    prometheus.write_text(prometheus_text,encoding='utf-8')
    prometheus.chmod(0o600)
    print('Prepared ignored runtime email files with TLS required. No connection or email was sent.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Do not print configuration values, raw subprocess output or secret contents.
        message = str(error) if isinstance(error, ValueError) else 'Email preparation failed; inspect local paths and permissions'
        raise SystemExit(message) from None
