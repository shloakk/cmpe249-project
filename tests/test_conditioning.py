import random
import unittest

from src.conditioning import EmpiricalCorruptor, uniform_corruption


class ConditioningTests(unittest.TestCase):
    def test_uniform_zero_keeps_truth(self):
        self.assertEqual(
            uniform_corruption("KEEP", "STRAIGHT", 0.0, random.Random(1)),
            ("KEEP", "STRAIGHT"),
        )

    def test_uniform_one_changes_pair(self):
        result = uniform_corruption("KEEP", "STRAIGHT", 1.0, random.Random(1))
        self.assertNotEqual(result, ("KEEP", "STRAIGHT"))

    def test_empirical_uses_observed_confusion(self):
        corruptor = EmpiricalCorruptor([{
            "gt_speed": "KEEP", "gt_path": "STRAIGHT",
            "pred_speed": "STOP", "pred_path": "STRAIGHT", "count": 3,
        }])
        self.assertEqual(corruptor.sample("KEEP", "STRAIGHT"), ("STOP", "STRAIGHT"))


if __name__ == "__main__":
    unittest.main()
