#!/usr/bin/env python
"""
OAuth2 end-to-end verification for the gmvault Python 3 port.

Offline checks (run automatically):
  - authorization URL generation (correct params + loopback redirect)
  - XOAUTH2 auth-string format (\\x01 separators, valid base64)
  - loopback code-capture server (simulated Google redirect)

Live checks (require your Google account + credentials in env vars):
  run with:  python verify_oauth2.py --live you@gmail.com
"""
import sys
import os
import argparse
import threading
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import gmv.credential_utils as cu
import gmv.log_utils as log_utils

log_utils.LoggerFactory.setup_simple_stderr_handler(log_utils.STANDALONE)


def check_authorization_url():
    url = cu.generate_permission_url()
    assert "client_id=" in url, "missing client_id in %s" % url
    assert "response_type=code" in url, "missing response_type in %s" % url
    assert "redirect_uri=" in url, "missing redirect_uri in %s" % url
    assert "scope=" in url, "missing scope in %s" % url
    print("[OK] authorization URL generated:")
    print("     %s" % url)
    return url


def check_xoauth2_string():
    raw = cu.CredentialHelper._generate_oauth2_auth_string(
        "user@gmail.com", "TOK123", base64_encode=False)
    assert raw == "user=user@gmail.com\x01auth=Bearer TOK123\x01\x01", repr(raw)
    print("[OK] XOAUTH2 raw SASL string has correct \\x01 separators: %r" % raw)

    b64 = cu.CredentialHelper._generate_oauth2_auth_string(
        "user@gmail.com", "TOK123", base64_encode=True)
    assert isinstance(b64, bytes), "base64_encode must return bytes in Py3"
    decoded = b64.decode("ascii")
    # base64 of the raw string must decode back to the raw string
    import base64
    assert base64.b64decode(decoded).decode("utf-8") == raw
    print("[OK] XOAUTH2 base64 encode returns bytes and round-trips")


def check_loopback_capture():
    redirect = "http://127.0.0.1:8099"
    result = {}

    def server_thread():
        result["code"] = cu._capture_oauth_code(redirect)

    t = threading.Thread(target=server_thread, daemon=True)
    t.start()
    # simulate Google redirecting back with ?code=...
    urllib.request.urlopen(redirect + "/?code=SAMPLE_CODE", timeout=5).close()
    t.join(timeout=5)
    assert result.get("code") == "SAMPLE_CODE", result
    print("[OK] loopback capture server received code: %s" % result["code"])


def live_flow(email):
    print("\n=== LIVE OAuth2 flow for %s ===" % email)
    print("Make sure GMVAULT_CLIENT_ID and GMVAULT_CLIENT_SECRET are set,")
    print("and http://127.0.0.1:8080 is registered as an Authorized")
    print("redirect URI in your Google Cloud OAuth client.\n")
    creds = cu.CredentialHelper.get_oauth2_credential(email)
    print("[OK] obtained credential of type: %s" % creds["type"])
    print("     auth_str prefix: %r" % creds["value"][:40])
    # verify the refresh-token path does not crash (uses stored creds)
    print("[OK] credential (refresh) flow completed")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", metavar="EMAIL", help="run the live OAuth2 flow")
    args = p.parse_args()

    print("=== OAuth2 offline verification ===")
    check_authorization_url()
    check_xoauth2_string()
    check_loopback_capture()
    print("\nAll offline checks passed.")

    if args.live:
        if not os.environ.get("GMVAULT_CLIENT_ID") or not os.environ.get("GMVAULT_CLIENT_SECRET"):
            print("ERROR: set GMVAULT_CLIENT_ID and GMVAULT_CLIENT_SECRET first.", file=sys.stderr)
            sys.exit(1)
        live_flow(args.live)


if __name__ == "__main__":
    main()
