import pickle
from pathlib import Path
import tempfile
import unittest

import numpy as np

from src.meta_actions import CAMERA_ORDER
from src.senna_cache.build_manifest import build


class ManifestTests(unittest.TestCase):
    def test_builds_six_camera_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cameras = {}
            for index, camera in enumerate(CAMERA_ORDER):
                image = root / "samples" / camera / f"{index}.jpg"
                image.parent.mkdir(parents=True, exist_ok=True)
                image.touch()
                cameras[camera] = {"data_path": str(image)}
            record = {
                "token": "sample-token",
                "cams": cameras,
                "gt_ego_fut_trajs": np.array([
                    [0, 2], [0, 2], [0, 2], [0, 2], [0, 2], [0, 2]
                ]),
                "gt_ego_fut_masks": np.ones(6),
                "gt_ego_fut_cmd": np.array([0, 0, 1]),
                "gt_ego_lcf_feat": np.array([0, 0, 0, 0, 0, 0, 0, 4]),
            }
            annotation = root / "infos.pkl"
            with annotation.open("wb") as handle:
                pickle.dump({"infos": [record]}, handle)
            result = build(annotation, root)
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]["images"]), 6)
            self.assertEqual(result[0]["gt_answer"], "KEEP, STRAIGHT")
            self.assertEqual(result[0]["navigation_command"], "go straight")

    def test_rejects_partial_future(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            annotation = root / "infos.pkl"
            record = {
                "cams": {}, "gt_ego_fut_trajs": np.ones((6, 2)),
                "gt_ego_fut_masks": np.array([1, 1, 1, 1, 1, 0]),
            }
            with annotation.open("wb") as handle:
                pickle.dump([record], handle)
            with self.assertRaises(RuntimeError):
                build(annotation, root, strict_files=False)


if __name__ == "__main__":
    unittest.main()
