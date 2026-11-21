from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VADTrainingLauncherTests(unittest.TestCase):
    def test_disables_upstream_in_training_validation(self):
        launcher = (ROOT / "scripts/hpc/vad_train_adapter.sbatch").read_text()
        self.assertIn("--no-validate", launcher)
        self.assertIn('"$vad_root/tools/train.py"', launcher)


if __name__ == "__main__":
    unittest.main()
