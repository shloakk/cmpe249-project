import unittest

from src.error_audit.analyze import audit


class AuditTests(unittest.TestCase):
    def test_metrics_include_parse_failures_in_denominator(self):
        rows = [
            {"gt_speed": "KEEP", "gt_path": "STRAIGHT", "pred_speed": "KEEP",
             "pred_path": "STRAIGHT", "parse_ok": True},
            {"gt_speed": "STOP", "gt_path": "STRAIGHT", "pred_speed": "KEEP",
             "pred_path": "STRAIGHT", "parse_ok": True},
            {"gt_speed": "STOP", "gt_path": "STRAIGHT", "pred_speed": None,
             "pred_path": None, "parse_ok": False},
        ]
        result = audit(rows)
        self.assertEqual(result["samples"], 3)
        self.assertAlmostEqual(result["parse_rate"], 2 / 3)
        self.assertAlmostEqual(result["joint_accuracy_all"], 1 / 3)
        self.assertAlmostEqual(result["actual_change_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
