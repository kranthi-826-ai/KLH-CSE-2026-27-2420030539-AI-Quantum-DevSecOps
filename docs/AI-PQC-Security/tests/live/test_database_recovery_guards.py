import importlib.util
import hashlib
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('recovery',Path(__file__).with_name('verify_database_recovery.py'))
recovery=importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)

class RecoveryGuards(unittest.TestCase):
    def test_numeric_database_error_is_retained_without_raw_error_text(self):
        error=recovery.MysqlFailure(b'ERROR 1062 (23000): duplicate secret-looking-fixture-value')
        self.assertEqual(error.code,1062)
        self.assertNotIn('secret-looking-fixture-value',str(error))
        self.assertIsNone(recovery.MysqlFailure(b'connection failure').code)

    def test_only_fixture_schema_names_are_allowed(self):
        for suffix in ('source','restored'):
            value='pqc_recovery_'+'a'*32+'_'+suffix
            self.assertEqual(recovery.checked_schema(value),value)
        for value in ('pqc_auth_db','mysql','pqc_recovery_short_source','pqc_recovery_'+'a'*32+'_restored\n',None):
            with self.subTest(value=value),self.assertRaises(ValueError):recovery.checked_schema(value)

    def test_corrupt_backup_is_refused(self):
        data=b'CREATE TABLE audit_outbox (id INT);'
        digest=hashlib.sha256(data).hexdigest()
        self.assertEqual(recovery.checked_dump(data,digest),data)
        with self.assertRaises(ValueError):recovery.checked_dump(data+b'changed',digest)

    def test_switching_dropping_and_definer_statements_are_refused(self):
        for data in (b'USE pqc_auth_db;',b'CREATE DATABASE accidental;',b'DROP TABLE audit_outbox;',
                     b'/*!50003 DEFINER=root */',b'SOURCE other.sql;'):
            with self.subTest(statement=data),self.assertRaises(ValueError):
                recovery.checked_dump(data,hashlib.sha256(data).hexdigest())

if __name__=='__main__':unittest.main()
