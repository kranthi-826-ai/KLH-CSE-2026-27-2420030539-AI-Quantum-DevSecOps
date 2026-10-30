import unittest
from verify_gateway_burst import validate_burst


class BurstVerifierTests(unittest.TestCase):
    def rows(self):
        return [{'status': status, 'retry_after': '5', 'cache_control': 'no-store',
                 'correlation_matches': True} for status in [401] * 10 + [429] * 2]

    def test_expected_burst(self):
        validate_burst(self.rows(), 1.0)

    def test_refilled_bucket_is_not_claimed_as_pass(self):
        with self.assertRaises(RuntimeError):
            validate_burst(self.rows(), 6)

    def test_forwarded_bypass_fails(self):
        rows = self.rows()
        rows[-1]['status'] = 401
        with self.assertRaises(RuntimeError):
            validate_burst(rows, 1)

    def test_missing_response_safety_headers_fail(self):
        for field, value in [('retry_after', '0'), ('cache_control', ''), ('correlation_matches', False)]:
            with self.subTest(field=field):
                rows = self.rows()
                rows[-1][field] = value
                with self.assertRaises(RuntimeError):
                    validate_burst(rows, 1)


if __name__ == '__main__':
    unittest.main()
