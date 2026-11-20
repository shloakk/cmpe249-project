from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VADRuntimeViewTests(unittest.TestCase):
    def test_creates_idempotent_isolated_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vad_root = root / "vad"
            data_root = root / "vad_data"
            runtime = root / "run/runtime"
            (vad_root / "projects").mkdir(parents=True)
            data_root.mkdir()
            command = [
                "bash",
                str(ROOT / "scripts/prepare_vad_runtime.sh"),
                str(runtime),
                str(vad_root),
                str(data_root),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual((runtime / "projects").resolve(),
                             (vad_root / "projects").resolve())
            self.assertEqual((runtime / "data/nuscenes").resolve(),
                             data_root.resolve())


if __name__ == "__main__":
    unittest.main()
