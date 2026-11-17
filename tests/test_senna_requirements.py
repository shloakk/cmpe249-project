import unittest

from src.senna_requirements import project


class InferenceProfileTests(unittest.TestCase):
    def test_preserves_official_versions_and_accounts_for_exclusions(self):
        included, excluded = project('torch==2.0.1+cu118\nNumPy==1.26.4\naidisdk==0.18.0\n', ['torch', 'numpy'])
        self.assertEqual(included, ['torch==2.0.1+cu118', 'NumPy==1.26.4'])
        self.assertEqual(excluded, ['aidisdk==0.18.0'])

    def test_normalizes_package_names(self):
        self.assertEqual(project('typing_extensions==4.11.0\n', ['typing-extensions'])[0], ['typing_extensions==4.11.0'])

    def test_cannot_invent_a_missing_pin(self):
        with self.assertRaisesRegex(ValueError, 'missing official pins'):
            project('torch==2.0.1+cu118\n', ['invented-package'])

    def test_rejects_unpinned_or_ambiguous_requirements(self):
        for text in ('numpy>=1.0', 'numpy==1.0\nnumpy==2.0', '--extra-index-url https://example.test'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    project(text, ['numpy'])

    def test_rejects_duplicate_selection(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate selected'):
            project('NumPy==1.26.4\n', ['numpy', 'NumPy'])
