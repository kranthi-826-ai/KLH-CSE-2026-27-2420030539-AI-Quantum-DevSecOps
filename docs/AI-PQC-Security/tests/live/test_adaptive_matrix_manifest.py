import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location('adaptive_matrix',Path(__file__).with_name('verify_adaptive_matrix.py'))
matrix=importlib.util.module_from_spec(spec);spec.loader.exec_module(matrix)

class MatrixManifestTests(unittest.TestCase):
    def test_frozen_cases_have_unique_ids_and_explicit_fail_closed_expectations(self):
        self.assertEqual(len(matrix.CASES),16)
        self.assertEqual(len({case[0] for case in matrix.CASES}),16)
        self.assertEqual(sum(case[-1]==422 for case in matrix.CASES),4)
        for case in matrix.CASES:
            _,_,_,_,_,risk,mode,status=case
            self.assertEqual(status==422,risk=='HIGH' and mode=='CLASSICAL')
    def test_both_selection_boundaries_and_real_4kib_payload_are_present(self):
        self.assertTrue({0,7,8,14,15,100}.issubset({case[4] for case in matrix.CASES}))
        self.assertEqual(len(matrix.prototype()['data'].encode()),4096)
        self.assertTrue(matrix.prototype()['networkFeatures'])

if __name__=='__main__':unittest.main()
