import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.config import NAMES, validate_paths


class PathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.env = dict(zip(NAMES, map(str, (
            root / 'data', root / 'derived', root / 'artifacts',
            root / 'artifacts/checkpoints', root / 'artifacts/hf',
        ))))
        for path in self.env.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        for name in ('samples', 'sweeps', 'maps', 'v1.0-trainval'):
            (Path(self.env[NAMES[0]]) / name).mkdir()

    def test_valid_and_no_dataset_mutation(self):
        root = Path(self.env[NAMES[0]])
        before = sorted(root.rglob('*'))
        self.assertEqual(len(validate_paths(self.env)), 5)
        self.assertEqual(before, sorted(root.rglob('*')))

    def test_required_variables(self):
        for name in NAMES:
            with self.subTest(name=name):
                env = self.env.copy()
                del env[name]
                with self.assertRaisesRegex(ValueError, name):
                    validate_paths(env)

    def test_relative_missing_and_placeholder(self):
        for value in ('relative', '/nonexistent/config-test-path', '/path/<user>'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_paths({**self.env, NAMES[0]: value})

    def test_missing_dataset_layout(self):
        (Path(self.env[NAMES[0]]) / 'maps').rmdir()
        with self.assertRaisesRegex(ValueError, 'missing directory maps'):
            validate_paths(self.env)

    def test_shared_output_overlap(self):
        for name in NAMES[2:]:
            for protected in NAMES[:2]:
                with self.subTest(name=name, protected=protected):
                    with self.assertRaisesRegex(ValueError, 'overlap'):
                        validate_paths({**self.env, name: self.env[protected]})

    def test_symlink_into_shared_data(self):
        link = Path(self.tmp.name) / 'link'
        link.symlink_to(self.env[NAMES[0]], target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'overlap'):
            validate_paths({**self.env, NAMES[2]: str(link)})

    def test_cache_outside_artifact(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        with self.assertRaisesRegex(ValueError, 'inside EXPERIMENT_ROOT'):
            validate_paths({**self.env, 'HF_HOME': str(outside)})

    def test_unwritable(self):
        real_access = os.access
        artifact = Path(self.env[NAMES[2]]).resolve()
        with patch('src.config.os.access', side_effect=lambda p, mode:
                   False if p == artifact and mode & os.W_OK else real_access(p, mode)):
            with self.assertRaisesRegex(ValueError, 'not writable'):
                validate_paths(self.env)

    def test_unreadable(self):
        with patch('src.config.os.access', return_value=False):
            with self.assertRaisesRegex(ValueError, 'not readable'):
                validate_paths(self.env)


if __name__ == '__main__':
    unittest.main()
