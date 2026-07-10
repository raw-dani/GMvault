"""
    Gmvault: a tool to backup and restore your gmail account.
    Copyright (C) <since 2011>  <guillaume Aubert (guillaume dot aubert at gmail do com)>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
"""
   Unit tests for GIMAPFetcher using mock IMAP client.
"""
import unittest
import sys
import os
from unittest.mock import patch

# Ensure src layout is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from gmv.tests.mock_imap_client import MockIMAPClient


class TestGIMAPFetcherWithMockClient(unittest.TestCase):
    """
       Test GIMAPFetcher using a mock IMAP client.
    """

    def _create_fetcher_with_mock(self):
        import gmv.imap_utils as imap_utils
        credential = {'type': 'passwd', 'value': 'test_password'}
        fetcher = imap_utils.GIMAPFetcher('imap.gmail.com', 993, 'test@example.com', credential)
        return fetcher

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_connect(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            self.assertTrue(fetcher.once_connected)
            self.assertIsNotNone(fetcher.server)
        finally:
            fetcher.disconnect()

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_get_capabilities(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            caps = fetcher.get_capabilities()
            self.assertIn('IMAP4REV1', caps)
        finally:
            fetcher.disconnect()

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_server_list_folders(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            folders = fetcher.server.list_folders()
            self.assertIsNotNone(folders)
            self.assertGreater(len(folders), 0)
        finally:
            fetcher.disconnect()

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_server_search_empty(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            ids = fetcher.server.search({'type': 'imap', 'req': 'ALL', 'charset': 'utf-8'})
            self.assertEqual(ids, [])
        finally:
            fetcher.disconnect()

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_server_append_and_search(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            res = fetcher.server.append('[Gmail]/All Mail', b'Test email body', ['\\Seen'], None)
            self.assertIsNotNone(res)
            self.assertIn('APPENDUID', res)

            ids = fetcher.server.search({'type': 'imap', 'req': 'ALL', 'charset': 'utf-8'})
            self.assertEqual(len(ids), 1)
        finally:
            fetcher.disconnect()

    @patch('gmv.imap_utils.mimap.MonkeyIMAPClient', new=MockIMAPClient)
    def test_server_fetch_message(self):
        fetcher = self._create_fetcher_with_mock()
        try:
            fetcher.connect()
            res = fetcher.server.append('[Gmail]/All Mail', b'Test email body', ['\\Seen'], None)
            uid = int(res.split(' ')[2])

            fetched = fetcher.fetch([uid], ['BODY[]', 'FLAGS'])
            self.assertIn(uid, fetched)
            self.assertEqual(fetched[uid]['BODY[]'], b'Test email body')
            self.assertEqual(fetched[uid]['FLAGS'], ['\\Seen'])
        finally:
            fetcher.disconnect()


if __name__ == '__main__':
    unittest.main()
