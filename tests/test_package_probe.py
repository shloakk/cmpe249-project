import builtins
import contextlib
import io
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

PROBE = Path(__file__).resolve().parents[1] / 'scripts/environments/probe.py'


class PackageProbeTests(unittest.TestCase):
    def test_package_check_does_not_import_torch_or_model_code(self):
        versions = {'torch': '1.9.1+cu111', 'torchvision': '0.10.1+cu111',
                    'mmcv-full': '1.4.0', 'mmdet': '2.14.0',
                    'mmsegmentation': '0.14.1', 'mmdet3d': '0.17.1'}
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name.split('.')[0] in ('torch', 'mmcv', 'mmdet', 'mmseg', 'mmdet3d', 'projects'):
                raise AssertionError(f'Package-only check imported runtime module {name}')
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            args = [str(PROBE), 'vad', '--packages-only', '--upstream', tmp]
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(sys, 'argv', args))
                stack.enter_context(patch.object(sys, 'path', list(sys.path)))
                stack.enter_context(patch('importlib.metadata.version', side_effect=versions.__getitem__))
                stack.enter_context(patch('builtins.__import__', side_effect=guarded_import))
                run = stack.enter_context(patch('subprocess.run'))
                output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(PROBE), run_name='__main__')
                self.assertEqual(result.exception.code, 0)
                self.assertIn('VAD_PACKAGES_OK', output.getvalue())
                self.assertEqual(run.call_count, 2)

    def test_wrong_version_fails_before_runtime_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(sys, 'argv', [str(PROBE), 'vad', '--packages-only', '--upstream', tmp]))
                stack.enter_context(patch.object(sys, 'path', list(sys.path)))
                stack.enter_context(patch('importlib.metadata.version', return_value='wrong'))
                run = stack.enter_context(patch('subprocess.run'))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                with self.assertRaisesRegex(SystemExit, 'expected 1.9.1'):
                    runpy.run_path(str(PROBE), run_name='__main__')
                run.assert_not_called()
