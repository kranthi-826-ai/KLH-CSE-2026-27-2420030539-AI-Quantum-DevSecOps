import copy
import hashlib
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import verify_concurrent_adaptive as probe


def fixture():
    rows, executions, policies, events = [], [], [], []
    for batch in range(probe.BATCHES):
        for name, sensitivity, _, _, risk, mode, status in probe.CASES:
            index = len(rows)
            correlation = f'fixture-{index}'
            decision, execution = f'decision-{index}', f'execution-{index}'
            rows.append(dict(batch=batch, case=name, correlation_id=correlation, sensitivity=sensitivity,
                             expected_http=status, actual_http=status, expected_mode=mode, expected_risk=risk,
                             execution_id=execution, decision_id=decision, passed=True))
            executions.append(dict(correlation=correlation, username='fixture', executionId=execution,
                decisionId=decision, mode=mode, risk=risk, score=.5690423129295029,
                modelVersion=probe.MODEL_SHA[:16], policyVersion='1.1.0',
                payloadHash=hashlib.sha256(probe.prototype()['data'].encode()).hexdigest(),
                outcome='SUCCESS' if status == 200 else 'FAILED', verified=int(status == 200), cryptoMillis=0))
            policies.append(dict(correlation=correlation, decisionId=decision, mode=mode, risk=risk,
                inputRisk='MEDIUM', sensitivity=sensitivity, modelVersion=probe.MODEL_SHA[:16], policyVersion='1.1.0'))
            events.append(dict(correlation=correlation, eventId=f'event-{index}', username='fixture',
                outcome='SUCCESS' if status == 200 else 'FAILURE',
                eventType='API_ACCESS_GRANTED' if status == 200 else 'API_ACCESS_DENIED'))
    return rows, executions, policies, events


class ConcurrentProbeTests(unittest.TestCase):
    def test_frozen_workload_has_all_modes_and_denial_without_large_burst(self):
        self.assertEqual((probe.BATCHES, probe.WORKERS), (6, 4))
        self.assertEqual(len(probe.CASES), 4)
        self.assertEqual([case[-1] for case in probe.CASES], [200, 200, 200, 422])
        self.assertEqual({case[-2] for case in probe.CASES}, {'CLASSICAL', 'HYBRID', 'PQC'})

    def test_overlap_requires_real_intersecting_client_intervals(self):
        self.assertEqual(probe.peak_overlap([dict(start_ms=0, end_ms=1), dict(start_ms=1, end_ms=2)]), 1)
        self.assertEqual(probe.peak_overlap([dict(start_ms=0, end_ms=2), dict(start_ms=1, end_ms=3)]), 2)

    def test_accepts_matching_audits_without_requiring_database_row_order(self):
        rows, executions, policies, events = fixture()
        probe.verify_audits(rows, list(reversed(executions)), policies, events, 'fixture')
        self.assertTrue(all(row['audit_verified'] for row in rows))

    def test_rejects_missing_duplicate_crossed_and_inconsistent_audits(self):
        for defect in ('missing', 'duplicate-correlation', 'crossed-decision', 'wrong-owner',
                       'wrong-model', 'wrong-payload', 'denial-crypto', 'wrong-event', 'crossed-response'):
            with self.subTest(defect=defect):
                rows, executions, policies, events = copy.deepcopy(fixture())
                if defect == 'missing':
                    events.pop()
                elif defect == 'duplicate-correlation':
                    executions[1]['correlation'] = executions[0]['correlation']
                elif defect == 'crossed-decision':
                    policies[0]['decisionId'], policies[1]['decisionId'] = policies[1]['decisionId'], policies[0]['decisionId']
                elif defect == 'wrong-owner':
                    executions[0]['username'] = 'other-user'
                elif defect == 'wrong-model':
                    policies[0]['modelVersion'] = 'different'
                elif defect == 'wrong-payload':
                    executions[0]['payloadHash'] = 'wrong'
                elif defect == 'denial-crypto':
                    executions[3]['cryptoMillis'] = 1
                elif defect == 'wrong-event':
                    events[3]['outcome'] = 'SUCCESS'
                elif defect == 'crossed-response':
                    rows[0]['execution_id'] = rows[1]['execution_id']
                with self.assertRaises(RuntimeError):
                    probe.verify_audits(rows, executions, policies, events, 'fixture')


if __name__ == '__main__':
    unittest.main()
