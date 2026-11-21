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
    def test_generated_configs_preserve_released_checkpoint_fidelity(self):
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
                "img_norm_cfg = dict(\n"
                "    mean=[123.675, 116.28, 103.53],\n"
                "    std=[58.395, 57.12, 57.375], to_rgb=True)\n"
                "data_root = 'data/nuscenes/'\n"
            )
            expected = [
                str((source.parent / "../datasets/custom_nus-3d.py").resolve()),
                str((source.parent / "../_base_/default_runtime.py").resolve()),
            ]
            for module in modules:
                with self.subTest(module=module.__name__):
                    result = module.absolutize_base_paths(text, source)
                    result = module.set_released_image_normalization(
                        result, source
                    )
                    namespace = {}
                    exec(result, namespace)
                    self.assertEqual(namespace["_base_"], expected)
                    self.assertEqual(
                        namespace["img_norm_cfg"],
                        {
                            "mean": [103.530, 116.280, 123.675],
                            "std": [1.0, 1.0, 1.0],
                            "to_rgb": False,
                        },
                    )


if __name__ == "__main__":
    unittest.main()
