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
   Mock IMAP client for unit tests.
   This class mimics the IMAPClient interface used by GIMAPFetcher.
"""
import imaplib
from datetime import datetime


class MockIMAPClient:
    """
       A mock IMAP client that implements the subset of IMAPClient
       API used by GIMAPFetcher for unit testing.
    """
    def __init__(self, host, port, use_uid=True, ssl=True, timeout=None):
        self.host = host
        self.port = port
        self.use_uid = use_uid
        self.ssl = ssl
        self.timeout = timeout
        self._imap = None
        self._selected_folder = None

    def login(self, username, password):
        self._imap = MockIMAPConnection()

    def oauth2_login(self, auth_string):
        self._imap = MockIMAPConnection()

    def logout(self):
        if self._imap:
            self._imap = None

    def enable_compression(self):
        pass

    def capabilities(self):
        return ('IMAP4REV1', 'UNSELECT', 'IDLE', 'NAMESPACE', 'QUOTA', 'ID',
                'XLIST', 'CHILDREN', 'X-GM-EXT-1', 'XYZZY', 'SASL-IR',
                'AUTH=XOAUTH2', 'COMPRESS=DEFLATE')

    def list_folders(self):
        return [
            ((), '/', 'INBOX'),
            ((), '/', '[Gmail]'),
            ('\\AllMail', '/', '[Gmail]/All Mail'),
            ('\\Drafts', '/', '[Gmail]/Drafts'),
            ((), '/', '[Gmail]/Sent Mail'),
            ((), '/', '[Gmail]/Starred'),
            ((), '/', '[Gmail]/Trash'),
            ((), '/', '[Gmail]/Chats'),
        ]

    def xlist_folders(self):
        return self.list_folders()

    def select_folder(self, folder, readonly=False):
        self._selected_folder = folder

    def folder_exists(self, folder):
        return True

    def create_folder(self, folder):
        return 'Success'

    def delete_folder(self, folder):
        return 'Success'

    def fetch(self, ids, attributes):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.fetch(ids, attributes)

    def append(self, folder, msg_bytes, flags, internal_time):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.append(folder, msg_bytes, flags, internal_time)

    def search(self, criteria):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.search(criteria)

    def delete_messages(self, ids):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.delete_messages(ids)

    def expunge(self):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.expunge()

    def store(self, id_list, flags, silent=False):
        if not self._imap:
            raise imaplib.IMAP4.error('Not connected')
        return self._imap.store(id_list, flags, silent)


class MockIMAPConnection:
    """
       In-memory mock IMAP connection used by MockIMAPClient.
    """
    def __init__(self):
        self.messages = {}
        self.next_uid = 1
        self.selected_folder = None

    def fetch(self, ids, attributes):
        result = {}
        for msg_id in ids:
            msg = self.messages.get(msg_id)
            if msg:
                result[msg_id] = msg
        return result

    def append(self, folder, msg_bytes, flags, internal_time):
        uid = self.next_uid
        self.next_uid += 1
        msg = {
            'BODY[]': msg_bytes,
            'FLAGS': flags or [],
            'INTERNALDATE': internal_time or datetime.now(),
            'UID': uid,
        }
        self.messages[uid] = msg
        return 'APPENDUID 1 %d (Success)' % uid

    def search(self, criteria):
        return list(self.messages.keys())

    def delete_messages(self, ids):
        for msg_id in ids:
            self.messages.pop(msg_id, None)
        return 'OK'

    def expunge(self):
        return 'OK'

    def store(self, id_list, flags, silent=False):
        return 'OK'
