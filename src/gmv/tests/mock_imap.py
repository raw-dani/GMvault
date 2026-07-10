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
   Mock IMAP server for unit tests.
"""
import socket
import threading
import time
import imaplib

class MockIMAPServer:
    """
       A simple mock IMAP server for unit testing.
       Implements just enough IMAP commands for gmvault tests.
    """
    def __init__(self, host='127.0.0.1', port=0):
        self.host = host
        self.port = port
        self.server_socket = None
        self.thread = None
        self.running = False
        self.mailboxes = {}
        self.current_mailbox = None
        self.next_id = 1
        self.lock = threading.Lock()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.port = self.server_socket.getsockname()[1]
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self.port

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _run(self):
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, client_socket):
        try:
            client_socket.settimeout(10.0)
            tag = 1
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    cmd = data.decode('utf-8', errors='ignore').strip()
                    response = self._process_command(cmd, tag)
                    tag += 1
                    if response:
                        client_socket.sendall(response.encode('utf-8'))
                except socket.timeout:
                    break
                except Exception:
                    break
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    def _process_command(self, cmd, tag):
        cmd_upper = cmd.upper()
        if cmd_upper.startswith('LOGIN'):
            return self._cmd_login(cmd, tag)
        elif cmd_upper.startswith('CAPABILITY'):
            return self._cmd_capability(cmd, tag)
        elif cmd_upper.startswith('LIST') or cmd_upper.startswith('XLIST'):
            return self._cmd_list(cmd, tag)
        elif cmd_upper.startswith('SELECT'):
            return self._cmd_select(cmd, tag)
        elif cmd_upper.startswith('FETCH'):
            return self._cmd_fetch(cmd, tag)
        elif cmd_upper.startswith('SEARCH'):
            return self._cmd_search(cmd, tag)
        elif cmd_upper.startswith('APPEND'):
            return self._cmd_append(cmd, tag)
        elif cmd_upper.startswith('LOGOUT'):
            return self._cmd_logout(cmd, tag)
        elif cmd_upper.startswith('NOOP'):
            return self._cmd_noop(cmd, tag)
        elif cmd_upper.startswith('STATUS'):
            return self._cmd_status(cmd, tag)
        elif cmd_upper.startswith('EXAMINE'):
            return self._cmd_select(cmd, tag)
        else:
            return self._response(tag, 'BAD', 'Unknown command')

    def _response(self, tag, status, text):
        return '%s %s %s\r\n' % (tag, status, text)

    def _cmd_login(self, cmd, tag):
        return self._response(tag, 'OK', 'LOGIN completed')

    def _cmd_capability(self, cmd, tag):
        return self._response(tag, 'OK', 'CAPABILITY completed')

    def _cmd_list(self, cmd, tag):
        folders = [
            ('(\\HasNoChildren)', '/', 'INBOX'),
            ('(\\HasNoChildren)', '/', '[Gmail]'),
            ('(\\AllMail \\HasNoChildren)', '/', '[Gmail]/All Mail'),
            ('(\\HasNoChildren)', '/', '[Gmail]/Drafts'),
            ('(\\HasNoChildren)', '/', '[Gmail]/Sent Mail'),
            ('(\\HasNoChildren)', '/', '[Gmail]/Starred'),
            ('(\\HasNoChildren)', '/', '[Gmail]/Trash'),
            ('(\\HasNoChildren)', '/', '[Gmail]/Chats'),
        ]
        lines = []
        for flags, delim, name in folders:
            lines.append('%s "%s" "%s"' % (flags, delim, name))
        result = '* LIST ' + ' '.join(lines) + '\r\n'
        result += self._response(tag, 'OK', 'LIST completed')
        return result

    def _cmd_select(self, cmd, tag):
        self.current_mailbox = 'INBOX'
        result = '* %d EXISTS\r\n' % len(self.mailboxes.get('INBOX', []))
        result += '* 0 RECENT\r\n'
        result += '* OK [UIDVALIDITY 123456789] UID validity\r\n'
        result += self._response(tag, 'OK', 'SELECT completed')
        return result

    def _cmd_fetch(self, cmd, tag):
        if not self.current_mailbox:
            return self._response(tag, 'BAD', 'No mailbox selected')
        msgs = self.mailboxes.get(self.current_mailbox, [])
        if not msgs:
            return self._response(tag, 'OK', 'FETCH completed')
        result = ''
        for msg in msgs:
            uid = msg.get('uid', 1)
            body = msg.get('body', b'')
            flags = msg.get('flags', [])
            internaldate = msg.get('internaldate', '01-Jan-2020 00:00:00 +0000')
            msgid = msg.get('msgid', '<test@example.com>')
            subject = msg.get('subject', 'Test')
            received = msg.get('received', 'by 1.2.3.4')
            headers = 'Message-ID: %s\r\nSubject: %s\r\nX-Gmail-Received: %s\r\n' % (msgid, subject, received)
            flags_str = ' '.join(flags) if flags else '\\Seen'
            result += '* %d FETCH (UID %d RFC822.SIZE %d FLAGS (%s) INTERNALDATE "%s" BODY[HEADER.FIELDS (MESSAGE-ID SUBJECT X-GMAIL-RECEIVED)] {%d}\r\n' % (
                uid, uid, len(body) + len(headers), flags_str, internaldate, len(headers))
            result += headers + '\r\n'
            result += 'BODY[] {%d}\r\n' % len(body)
            result += body.decode('utf-8', errors='replace') if isinstance(body, bytes) else body
            result += '\r\n'
            result += ')\r\n'
        result += self._response(tag, 'OK', 'FETCH completed')
        return result

    def _cmd_search(self, cmd, tag):
        msgs = self.mailbox.get('INBOX', [])
        ids = ' '.join([str(msg.get('uid', 1)) for msg in msgs])
        result = '* SEARCH %s\r\n' % ids
        result += self._response(tag, 'OK', 'SEARCH completed')
        return result

    def _cmd_append(self, cmd, tag):
        with self.lock:
            uid = self.next_id
            self.next_id += 1
        msg = {
            'uid': uid,
            'body': b'',
            'flags': [],
            'internaldate': '01-Jan-2020 00:00:00 +0000',
            'msgid': '<mock-%d@example.com>' % uid,
            'subject': 'Mock Email %d' % uid,
            'received': 'by mock.server',
        }
        if 'INBOX' not in self.mailboxes:
            self.mailboxes['INBOX'] = []
        self.mailboxes['INBOX'].append(msg)
        return self._response(tag, 'OK', '[APPENDUID 1 %d] (Success)' % uid)

    def _cmd_logout(self, cmd, tag):
        return '* BYE IMAP4rev1 Server logging out\r\n' + self._response(tag, 'OK', 'LOGOUT completed')

    def _cmd_noop(self, cmd, tag):
        return self._response(tag, 'OK', 'NOOP completed')

    def _cmd_status(self, cmd, tag):
        return self._response(tag, 'OK', 'STATUS completed')

    def add_message(self, uid, body, flags=None, internaldate=None, msgid=None, subject=None, received=None):
        with self.lock:
            if 'INBOX' not in self.mailboxes:
                self.mailboxes['INBOX'] = []
            self.mailboxes['INBOX'].append({
                'uid': uid,
                'body': body,
                'flags': flags or [],
                'internaldate': internaldate or '01-Jan-2020 00:00:00 +0000',
                'msgid': msgid or '<mock-%d@example.com>' % uid,
                'subject': subject or 'Mock Email %d' % uid,
                'received': received or 'by mock.server',
            })
            if uid >= self.next_id:
                self.next_id = uid + 1

    def clear_mailbox(self):
        with self.lock:
            self.mailboxes['INBOX'] = []
            self.next_id = 1
