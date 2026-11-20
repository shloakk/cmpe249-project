import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VADConfigPathTests(unittest.TestCase):
    def test_generated_configs_use_absolute_base_paths(self):
        modules = [
            load_module("prepare_vad_baseline", ROOT / "scripts/prepare_vad_baseline.py"),
            load_module("prepare_vad_condition", ROOT / "integrations/vad/prepare_config.py"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "projects/configs/VAD/example.py"
            source.parent.mkdir(parents=True)
            text = (
                "_base_ = [\n"
                "    '../datasets/custom_nus-3d.py',\n"
                "    '../_base_/default_runtime.py',\n"
                "]\n"
                "data_root = 'data/nuscenes/'\n"
            )
            expected = [
                str((source.parent / "../datasets/custom_nus-3d.py").resolve()),
                str((source.parent / "../_base_/default_runtime.py").resolve()),
            ]
            for module in modules:
                with self.subTest(module=module.__name__):
                    result = module.absolutize_base_paths(text, source)
                    namespace = {}
                    exec(result, namespace)
                    self.assertEqual(namespace["_base_"], expected)


if __name__ == "__main__":
    unittest.main()
