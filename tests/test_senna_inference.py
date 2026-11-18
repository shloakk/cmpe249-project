import unittest

from src.senna_cache.run_inference import validate_multiview_manifest


class SennaInferenceTests(unittest.TestCase):
    def test_accepts_one_token_per_camera(self):
        sample = {"images": [str(index) for index in range(6)],
                  "question": "\n".join(["<image>"] * 6)}
        validate_multiview_manifest([sample])

    def test_rejects_text_only_manifest(self):
        sample = {"images": [str(index) for index in range(6)],
                  "question": "plan the next three seconds"}
        with self.assertRaisesRegex(ValueError, "paths=6 tokens=0"):
            validate_multiview_manifest([sample])


if __name__ == "__main__":
    unittest.main()
