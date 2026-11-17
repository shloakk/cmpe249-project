import unittest

from src.vad_metrics import aggregate


class VADMetricTests(unittest.TestCase):
    def test_ignores_invalid_future(self):
        base = {
            "plan_L2_1s": 1, "plan_L2_2s": 2, "plan_L2_3s": 3,
            "plan_obj_col_1s": 0, "plan_obj_col_2s": 0, "plan_obj_col_3s": 1,
            "plan_obj_box_col_1s": 0, "plan_obj_box_col_2s": 1,
            "plan_obj_box_col_3s": 1,
        }
        valid = dict(base, fut_valid_flag=True)
        invalid = dict(base, fut_valid_flag=False, plan_L2_1s=100)
        result = aggregate([{"metric_results": valid}, {"metric_results": invalid}])
        self.assertEqual(result["valid_samples"], 1)
        self.assertEqual(result["plan_L2_1s"], 1)


if __name__ == "__main__":
    unittest.main()
