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
   Unit tests using mock IMAP server and mock OAuth2 endpoints.
"""
import unittest
import json
import sys
import os
import time
import threading

# Ensure src layout is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from gmv.tests.mock_imap import MockIMAPServer
from gmv.tests.mock_oauth2 import MockOAuth2Server


class TestMockIMAPServer(unittest.TestCase):
    """
       Test the mock IMAP server
    """

    def setUp(self):
        self.server = MockIMAPServer(port=0)
        self.port = self.server.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.stop()

    def test_server_starts_and_stops(self):
        self.assertGreater(self.port, 0)

    def test_add_and_retrieve_message(self):
        self.server.add_message(
            uid=1,
            body=b'Test email body',
            flags=['\\Seen'],
            internaldate='01-Jan-2020 00:00:00 +0000',
            msgid='<test1@example.com>',
            subject='Test Subject',
            received='by 1.2.3.4',
        )
        self.assertEqual(len(self.server.mailboxes.get('INBOX', [])), 1)

    def test_clear_mailbox(self):
        self.server.add_message(uid=1, body=b'Body')
        self.server.clear_mailbox()
        self.assertEqual(len(self.server.mailboxes.get('INBOX', [])), 0)


class TestMockOAuth2Server(unittest.TestCase):
    """
       Test the mock OAuth2 server
    """

    def setUp(self):
        self.server = MockOAuth2Server(port=0)
        self.base_url = self.server.start()
        time.sleep(0.5)

    def tearDown(self):
        self.server.stop()

    def test_server_starts(self):
        self.assertIn('http://', self.base_url)

    def test_authorization_code_grant(self):
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': 'test_code',
            'client_id': 'test_client',
            'client_secret': 'test_secret',
        }).encode('utf-8')

        req = urllib.request.Request(self.base_url, data=params, method='POST')
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        self.assertEqual(data['access_token'], 'mock_access_token_test_code')
        self.assertEqual(data['refresh_token'], 'mock_refresh_token_test_code')
        self.assertEqual(data['expires_in'], 3600)

    def test_refresh_token_grant(self):
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': 'test_refresh',
            'client_id': 'test_client',
            'client_secret': 'test_secret',
        }).encode('utf-8')

        req = urllib.request.Request(self.base_url, data=params, method='POST')
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        self.assertEqual(data['access_token'], 'mock_access_token_refreshed')
        self.assertEqual(data['expires_in'], 3600)


if __name__ == '__main__':
    unittest.main()
