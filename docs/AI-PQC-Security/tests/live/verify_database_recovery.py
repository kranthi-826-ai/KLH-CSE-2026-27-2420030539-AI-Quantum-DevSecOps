"""Isolated MySQL audit backup/restore rehearsal. Never restores into application databases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
BIN = Path(r'C:\Program Files\MySQL\MySQL Server 9.7\bin')
TABLES = {'audit_outbox':'pqc_auth_db', 'audit_outbox_replay_log':'pqc_auth_db',
          'security_events':'pqc_monitoring_db', 'crypto_executions':'pqc_business_db'}
SCHEMA = re.compile(r'pqc_recovery_[0-9a-f]{32}_(source|restored)\Z')


class MysqlFailure(RuntimeError):
    def __init__(self, stderr):
        match=re.search(rb'ERROR (\d{4})\b',stderr)
        self.code=int(match.group(1)) if match else None
        super().__init__('MySQL fixture operation failed; raw errors/credentials are not included')


def checked_schema(name):
    if not isinstance(name,str) or not SCHEMA.fullmatch(name):
        raise ValueError('Only newly generated recovery-fixture schemas are allowed')
    return name


def checked_dump(data, expected_hash):
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError('Backup checksum mismatch; restore refused before database access')
    text = data.decode('utf-8')
    # This rehearsal has plain tables only, no routines/triggers or database switching.
    if re.search(r'\b(?:USE\s+|CREATE\s+DATABASE|DROP\s+|DEFINER\s*=|SOURCE\s+)', text, re.I):
        raise ValueError('Backup contains an unsupported database-switching or destructive statement')
    return data


def read_password():
    values = []
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        key, separator, value = line.partition('=')
        if separator and key.strip() == 'DB_PASSWORD':
            value = value.strip()
            if len(value)>=2 and value[0]==value[-1] and value[0] in "\"'": value=value[1:-1]
            values.append(value)
    if len(values)!=1 or not values[0] or '\x00' in values[0]:
        raise ValueError('Supply one DB_PASSWORD in the ignored root .env; it will not be printed')
    return values[0]


class Mysql:
    def __init__(self, password):
        self.environment = {**os.environ,'MYSQL_PWD':password}

    def command(self, executable, args, data=None):
        result = subprocess.run([str(BIN / executable),'--host=127.0.0.1','--port=3306','--user=root',
            '--default-character-set=utf8mb4',*args],input=data,capture_output=True,
            env=self.environment,timeout=15)
        if result.returncode:
            raise MysqlFailure(result.stderr)
        return result.stdout

    def sql(self, statement, schema=None):
        args = ['--batch','--skip-column-names']
        if schema is not None: args += ['--database='+checked_schema(schema)]
        return self.command('mysql.exe',args,statement.encode()).decode('utf-8').strip()

    def definition(self, schema, table, *, live=False):
        if table not in TABLES or (live and TABLES[table]!=schema):
            raise ValueError('Only fixed application audit table structures may be read')
        if not live: checked_schema(schema)
        raw = self.command('mysql.exe',['--batch','--raw','--skip-column-names'],
            f'SHOW CREATE TABLE `{schema}`.`{table}`;'.encode()).decode('utf-8').strip()
        ddl = raw.partition('\t')[2]
        if not ddl.startswith(f'CREATE TABLE `{table}` (') or 'ENGINE=InnoDB' not in ddl or re.search(r'REFERENCES|DEFINER',ddl,re.I):
            raise ValueError('Unsupported audit schema; review schema/version before recovery test')
        return ddl

    def dump(self, schema, *, data_only=False):
        checked_schema(schema)
        flags = ['--single-transaction','--skip-lock-tables','--no-tablespaces','--skip-comments',
            '--skip-add-drop-table','--skip-add-locks','--skip-triggers','--skip-extended-insert',
            '--skip-disable-keys','--set-gtid-purged=OFF','--column-statistics=0','--hex-blob']
        if data_only: flags += ['--no-create-info','--compact']
        return self.command('mysqldump.exe',[*flags,schema,*sorted(TABLES)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory',type=Path,required=True)
    args=parser.parse_args()
    folder=args.output_directory.resolve()
    if folder.exists() or folder.parent!=(ROOT/'ml/artifacts').resolve():
        raise ValueError('Use a new immediate child of the project artifacts directory')
    if not all((BIN/name).is_file() for name in ('mysql.exe','mysqldump.exe')):
        raise ValueError('Expected local MySQL tools are unavailable')
    db=Mysql(read_password())
    run=uuid.uuid4().hex
    source=checked_schema('pqc_recovery_'+run+'_source')
    target=checked_schema('pqc_recovery_'+run+'_restored')
    folder.mkdir()
    result={'schema':'isolated-audit-recovery-v1','passed':False,'checks':[],
        'synthetic_rows_only':True,'live_data_copied':False,'live_databases_written':False,
        'source_fixture':source,'restored_fixture':target,'fixtures_retained':True}
    started=time.monotonic()
    def check(name, condition):
        if not condition: raise RuntimeError('Recovery check failed: '+name)
        result['checks'].append(name)
    try:
        # Only SHOW CREATE on live tables. No live row reads, dumps, writes or account changes.
        definitions={table:db.definition(schema,table,live=True) for table,schema in TABLES.items()}
        result['server_version']=db.sql('SELECT VERSION();')
        for schema in (source,target):
            # Deliberately no IF NOT EXISTS: never reuse a schema, even on a UUID collision.
            db.sql(f'CREATE DATABASE `{schema}` CHARACTER SET utf8mb4;')
        check('fresh_restore_target_empty',db.sql('SHOW TABLES;',target)=='')
        for ddl in definitions.values(): db.sql(ddl+';',source)
        ids=[str(uuid.uuid4()) for _ in range(6)]
        fixtures=[]
        for index,status in enumerate(('PENDING','DEAD','DELIVERED')):
            fixtures.append(f"INSERT INTO audit_outbox(event_id,occurred_at_seconds,occurred_at_nanos,event_type,outcome,source_service,username,correlation_id,status,attempts,next_attempt_millis,delivered_at_millis,last_error_code) VALUES ('{ids[index]}',1700000000,123456789,'API_ACCESS_GRANTED','SUCCESS','synthetic-recovery-probe','fixture-user','fixture-correlation','{status}',{index},1700000000000,{1700000000001 if status=='DELIVERED' else 'NULL'},{chr(39)+'DELIVERY_UNAVAILABLE'+chr(39) if status=='DEAD' else 'NULL'});")
        fixtures += [f"INSERT INTO audit_outbox_replay_log(operation_id,event_id,operator_name,reason,requested_at_millis,previous_attempts,previous_error_code) VALUES ('{ids[3]}','{ids[1]}','synthetic-operator','RESTORED_DEPENDENCY',1700000000002,2,'DELIVERY_UNAVAILABLE');",
            f"INSERT INTO security_events(event_id,occurred_at,event_type,outcome,source_service,username,correlation_id,detail) VALUES ('{ids[4]}','2026-10-20 10:00:00.123456','API_ACCESS_GRANTED','SUCCESS','synthetic-recovery-probe','fixture-user','fixture-correlation','Synthetic recovery rehearsal — no real user data');",
            f"INSERT INTO crypto_executions(execution_id,executed_at,correlation_id,username,payload_sha256,risk_score,policy_latency_millis,crypto_latency_millis,total_latency_millis,round_trip_verified,outcome,selected_mode,model_version,policy_version) VALUES ('{ids[5]}','2026-10-20 10:00:00.654321','fixture-correlation','fixture-user','{'0'*64}',0.2,1,2,3,1,'SUCCESS','PQC','synthetic-no-inference','synthetic-no-crypto');"]
        db.sql('START TRANSACTION;'+''.join(fixtures)+'COMMIT;',source)
        data_before=db.dump(source,data_only=True)
        backup=db.dump(source)
        backup_hash=hashlib.sha256(backup).hexdigest()
        checked_dump(backup,backup_hash)
        path=folder/'synthetic-audit-backup.sql'
        path.write_bytes(backup)
        path.chmod(0o600)
        # Corruption must fail before any import. Do not try a corrupted restore.
        try: checked_dump(backup+b'\ncorruption',backup_hash)
        except ValueError: result['checks'].append('corrupted_backup_refused_before_restore')
        else: raise RuntimeError('Corruption guard failed')
        db.command('mysql.exe',['--database='+target],checked_dump(path.read_bytes(),backup_hash))
        check('all_fixture_rows_match',data_before==db.dump(target,data_only=True))
        check('all_table_definitions_match',all(db.definition(source,t)==db.definition(target,t) for t in TABLES))
        expected={'audit_outbox':3,'audit_outbox_replay_log':1,'security_events':1,'crypto_executions':1}
        counts={table:int(db.sql(f'SELECT COUNT(*) FROM `{table}`;',target)) for table in TABLES}
        check('row_counts_match',counts==expected)
        check('queue_states_preserved',db.sql('SELECT status FROM audit_outbox ORDER BY status;',target).splitlines()==['DEAD','DELIVERED','PENDING'])
        check('nanosecond_occurrence_preserved',db.sql('SELECT MIN(occurred_at_nanos) FROM audit_outbox;',target)=='123456789')
        # Re-inserting the same stable identity must fail after restore, not duplicate it.
        try: db.sql(fixtures[4],target)
        except MysqlFailure as error:
            check('restored_unique_event_identity_rejects_duplicate',error.code==1062)
        else: raise RuntimeError('Restored identity uniqueness was lost')
        check('failed_duplicate_did_not_change_rows',data_before==db.dump(target,data_only=True))
        result.update(passed=True,backup_sha256=backup_hash,backup_bytes=len(backup),
            restored_row_counts=counts,data_dump_sha256=hashlib.sha256(data_before).hexdigest())
    except Exception as error:
        result['error']=str(error) if isinstance(error,(ValueError,RuntimeError)) else type(error).__name__
        raise
    finally:
        result['seconds']=round(time.monotonic()-started,2)
        (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Verified isolated synthetic MySQL audit backup/restore. Live data untouched; test schemas and ignored evidence retained. No background server started.')


if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
        raise SystemExit(str(error) if isinstance(error,(ValueError,RuntimeError)) else
                         'Recovery rehearsal failed; raw credentials/errors are not included') from None
