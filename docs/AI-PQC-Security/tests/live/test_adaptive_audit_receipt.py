import copy
import importlib.util
from pathlib import Path
import sys
import unittest
import uuid

sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location('audit_check',Path(__file__).with_name('recheck_adaptive_audits.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def fixture():
    rows=[]
    for case in module.CASES:
        for repeat in range(2):
            rows.append({'case':case[0],'repeat':repeat,'passed':True,'actual_http':case[-1],
                'expected_mode':case[-2],'expected_effective_risk':case[-3],'selection_threshold_ms':case[4],
                'correlation_id':f"matrix-{'a'*32}-{repeat}-{case[0]}",
                'execution_id':str(uuid.uuid4()),'decision_id':str(uuid.uuid4())})
    return {'passed':True,'model_sha256':module.MODEL_SHA,'rows':rows}

class AuditReceiptTests(unittest.TestCase):
    def test_validates_complete_frozen_synthetic_identity_set(self):
        self.assertEqual(len(module.validate_receipt(fixture())),32)
    def test_rejects_incomplete_duplicate_changed_and_unsafe_receipts(self):
        for change in ('incomplete','duplicate','status','identity','correlation','mixed_run','mode'):
            receipt=fixture()
            if change=='incomplete':receipt['rows'].pop()
            elif change=='duplicate':receipt['rows'][1]=copy.deepcopy(receipt['rows'][0])
            elif change=='status':receipt['rows'][0]['actual_http']=500
            elif change=='identity':receipt['rows'][0]['execution_id']="unsafe' OR 1=1"
            elif change=='correlation':receipt['rows'][0]['correlation_id']="unsafe' OR 1=1"
            elif change=='mixed_run':receipt['rows'][0]['correlation_id']=receipt['rows'][0]['correlation_id'].replace('a'*32,'b'*32)
            else:receipt['rows'][0]['expected_mode']='CLASSICAL'
            with self.subTest(change=change),self.assertRaises(ValueError):module.validate_receipt(receipt)

if __name__=='__main__':unittest.main()
