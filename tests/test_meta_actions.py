import unittest

from src.meta_actions import parse_prediction, path_label, speed_label


class MetaActionTests(unittest.TestCase):
    def test_speed_rules(self):
        self.assertEqual(speed_label([(0, 0), (0, 0.2), (0, 0.4)]), "STOP")
        self.assertEqual(speed_label([(0, 0), (0, 2), (0, 4)]), "KEEP")
        self.assertEqual(speed_label([(0, 0), (0, 1), (0, 4)]), "ACCELERATE")
        self.assertEqual(speed_label([(0, 0), (0, 3), (0, 4)]), "DECELERATE")

    def test_path_rules(self):
        self.assertEqual(path_label([(0, 1), (0, 8)]), "STRAIGHT")
        self.assertEqual(path_label([(1, 1), (5, 5)]), "RIGHT_TURN")
        self.assertEqual(path_label([(-1, 1), (-5, 5)]), "LEFT_TURN")

    def test_parser_requires_one_label_per_axis(self):
        self.assertEqual(parse_prediction("KEEP, LEFT_CHANGE"), ("KEEP", "LEFT_CHANGE"))
        self.assertEqual(parse_prediction("Speed: stop; path: straight."), ("STOP", "STRAIGHT"))
        self.assertEqual(parse_prediction("KEEP or STOP, STRAIGHT"), (None, "STRAIGHT"))


if __name__ == "__main__":
    unittest.main()
