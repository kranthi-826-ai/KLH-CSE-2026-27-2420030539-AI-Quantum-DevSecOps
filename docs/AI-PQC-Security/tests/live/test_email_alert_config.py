import importlib.util
import json
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[2]/'scripts/email_alert_config.py'
spec=importlib.util.spec_from_file_location('email_alert_config',path)
config=importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

class EmailConfigTests(unittest.TestCase):
    def settings(self):
        return {'SMTP_HOST':'smtp.example.test','SMTP_PORT':'587','SMTP_FROM':'alerts@example.test',
                'SMTP_USERNAME':'fixture-user','SMTP_PASSWORD':'synthetic-test-password','ALERT_EMAIL_TO':'operator@example.test'}
    def text(self, values):
        return '\n'.join(f'{key}={value}' for key,value in values.items())
    def test_secret_stays_out_of_config_and_tls_is_required(self):
        settings=self.settings()
        result=config.alertmanager_document(settings,'/secrets/smtp-password')
        self.assertNotIn(settings['SMTP_PASSWORD'],json.dumps(result))
        self.assertTrue(result['global']['smtp_require_tls'])
        self.assertNotIn('insecure_skip_verify',json.dumps(result))
        self.assertTrue(result['receivers'][0]['email_configs'][0]['send_resolved'])
    def test_duplicate_missing_unknown_and_control_fields_are_rejected(self):
        for text in (self.text(self.settings())+'\nSMTP_HOST=duplicate', 'SMTP_HOST=one',
                     self.text(self.settings())+'\nUNKNOWN=value',self.text({**self.settings(),'SMTP_PASSWORD':'bad\x00value'})):
            with self.subTest(text_length=len(text)),self.assertRaises(ValueError):
                config.parse_settings(text)
    def test_invalid_addresses_hosts_ports_and_template_injection_are_rejected(self):
        for field,value in [('SMTP_HOST','https://smtp.example.test'),('SMTP_PORT','0'),('SMTP_PORT','65536'),
                            ('SMTP_PORT','not-a-port'),('SMTP_FROM','{{ .Status }}@example.test'),
                            ('ALERT_EMAIL_TO','one@example.test,two@example.test')]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                config.parse_settings(self.text({**self.settings(),field:value}))
    def test_implicit_tls_port_is_explicit(self):
        result=config.alertmanager_document({**self.settings(),'SMTP_PORT':'465'},'/secrets/password')
        self.assertTrue(result['global']['smtp_force_implicit_tls'])
        self.assertTrue(result['global']['smtp_require_tls'])
    def test_base_scrape_config_and_rule_holds_are_not_changed(self):
        base='global:\n  scrape_interval: 15s\nrule_files: [audit-alerts.yml]\n'
        result=config.prometheus_email_config(base)
        self.assertTrue(result.startswith(base.rstrip()))
        self.assertIn('alertmanager:9093',result)
        with self.assertRaises(ValueError):config.prometheus_email_config('alerting:\n  alertmanagers: []\n')
    def test_quoted_password_with_equals_is_preserved(self):
        settings=self.settings()
        text=self.text({**settings,'SMTP_PASSWORD':'"a=b=c"'})
        self.assertEqual(config.parse_settings(text)['SMTP_PASSWORD'],'a=b=c')

if __name__=='__main__':unittest.main()
