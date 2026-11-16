import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.upstream import verify


class ProvenanceTests(unittest.TestCase):
    def test_verifies_commit_clean_tree_and_file_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'requirements.txt').write_bytes(b'torch==example\n')
            entry = {'commit': 'a' * 40, 'files': {
                'requirements.txt': hashlib.sha256(b'torch==example\n').hexdigest()}}
            with patch('src.upstream.git', side_effect=['a' * 40, '']):
                verify(root, entry)
            for output, error in [(['b' * 40], 'unexpected upstream commit'),
                                  (['a' * 40, ' M requirements.txt'], 'dirty upstream')]:
                with self.subTest(error=error):
                    with patch('src.upstream.git', side_effect=output):
                        with self.assertRaisesRegex(ValueError, error):
                            verify(root, entry)
            (root / 'requirements.txt').write_text('changed')
            with patch('src.upstream.git', side_effect=['a' * 40, '']):
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    verify(root, entry)


if __name__ == '__main__':
    unittest.main()
