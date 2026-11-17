import io
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from src.network_check import check, main


class NetworkTests(unittest.TestCase):
    def test_head_and_timeout(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch('src.network_check.urllib.request.urlopen', return_value=response) as request:
            self.assertTrue(check('test', 'https://example.test')['reachable'])
        args, kwargs = request.call_args
        self.assertEqual(args[0].get_method(), 'HEAD')
        self.assertEqual(kwargs['timeout'], 10)

    def test_network_failure_is_reported(self):
        with patch('src.network_check.urllib.request.urlopen', side_effect=URLError('timeout')):
            result = check('test', 'https://example.test')
        self.assertFalse(result['reachable'])
        self.assertIn('timeout', result['error'])

    def test_only_file_host_accepts_not_found(self):
        error = HTTPError('https://example.test', 404, 'not found', {}, None)
        with patch('src.network_check.urllib.request.urlopen', side_effect=error):
            self.assertFalse(check('index', 'https://example.test')['reachable'])
            self.assertTrue(check('files', 'https://example.test', True)['reachable'])

    def test_proxy_denial_is_failure(self):
        error = HTTPError('https://example.test', 403, 'denied', {}, None)
        with patch('src.network_check.urllib.request.urlopen', side_effect=error):
            self.assertFalse(check('files', 'https://example.test', True)['reachable'])

    def test_any_failure_blocks_gate(self):
        with patch('src.network_check.check', return_value={'reachable': False}):
            with patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(main(), 1)
        self.assertIn('PACKAGE_NETWORK_BLOCKED', output.getvalue())
