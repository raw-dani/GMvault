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
   Mock OAuth2 endpoints for unit tests.
"""
import json
import threading
import http.server
import urllib.parse
import sys

class MockOAuth2Handler(http.server.BaseHTTPRequestHandler):
    """
       Mock OAuth2 token endpoint handler.
    """
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(body)

        grant_type = params.get('grant_type', [None])[0]
        client_id = params.get('client_id', [None])[0]
        client_secret = params.get('client_secret', [None])[0]

        if grant_type == 'authorization_code':
            code = params.get('code', [None])[0]
            if code and client_id and client_secret:
                response = {
                    'access_token': 'mock_access_token_%s' % code,
                    'expires_in': 3600,
                    'refresh_token': 'mock_refresh_token_%s' % code,
                    'token_type': 'Bearer',
                }
                self._send_json(200, response)
            else:
                self._send_json(400, {'error': 'invalid_request', 'error_description': 'Missing code, client_id or client_secret'})

        elif grant_type == 'refresh_token':
            refresh_token = params.get('refresh_token', [None])[0]
            if refresh_token and client_id and client_secret:
                response = {
                    'access_token': 'mock_access_token_refreshed',
                    'expires_in': 3600,
                    'token_type': 'Bearer',
                }
                self._send_json(200, response)
            else:
                self._send_json(400, {'error': 'invalid_request', 'error_description': 'Missing refresh_token, client_id or client_secret'})

        else:
            self._send_json(400, {'error': 'unsupported_grant_type', 'error_description': 'Unknown grant type: %s' % grant_type})

    def do_GET(self):
        self._send_json(404, {'error': 'not_found'})

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, *args):
        pass

class MockOAuth2Server:
    """
       Mock OAuth2 token server for unit tests.
    """
    def __init__(self, host='127.0.0.1', port=0):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.base_url = None

    def start(self):
        self.server = http.server.HTTPServer((self.host, self.port), MockOAuth2Handler)
        self.port = self.server.server_address[1]
        self.base_url = 'http://%s:%d' % (self.host, self.port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.base_url

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
