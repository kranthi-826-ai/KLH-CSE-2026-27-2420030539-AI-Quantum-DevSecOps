import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).parent))
from dashboard_fault_proxy import inject


class DashboardFaultGuards(unittest.TestCase):
    def test_only_reviewed_successful_read_sources_are_replaced(self):
        self.assertTrue(inject('malformed-events','/api/v1/events',200))
        self.assertFalse(inject('malformed-events','/api/v1/business/executions',200))
        self.assertTrue(inject('malformed-both','/api/v1/business/executions',200))
        for status in [400,401,403,429,500,502,503]:
            self.assertFalse(inject('malformed-both','/api/v1/events',status))
        for path in ['/api/v1/auth/login','/api/v1/business/adaptive-secure-data','/unrelated']:
            self.assertFalse(inject('malformed-both',path,200))
        self.assertFalse(inject('healthy','/api/v1/events',200))
        with self.assertRaises(ValueError):
            inject('unreviewed','/api/v1/events',200)


if __name__ == '__main__':
    unittest.main()
