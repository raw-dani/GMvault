# Rencana Update Aplikasi Gmvault — Porting Python 2 ke Python 3

## Informasi Dokumen

| Item | Detail |
|---|---|
| **Aplikasi** | Gmvault v1.9.1 |
| **Versi Plan** | 1.0 |
| **Target** | Python 3.11+ (Windows/Linux/macOS) |
| **Estimasi Total** | 4-6 minggu (developer full-time) |

---

## Daftar Isi

1. [Lingkup Pekerjaan](#1-lingkup-pekerjaan)
2. [Tahapan Pekerjaan](#2-tahapan-pekerjaan)
3. [Rincian Perubahan Per File](#3-rincian-perubahan-per-file)
4. [Dependency Updates](#4-dependency-updates)
5. [Perubahan Autentikasi OAuth2](#5-perubahan-autentikasi-oauth2)
6. [Perubahan IMAP & Jaringan](#6-perubahan-imap--jaringan)
7. [Perubahan Storage & Enkripsi](#7-perubahan-storage--enkripsi)
8. [Testing Strategy](#8-testing-strategy)
9. [Risiko & Mitigasi](#9-risiko--mitigasi)
10. [Roadmap Timeline](#10-roadmap-timeline)
11. [Referensi](#11-referensi)

---

## 1. Lingkup Pekerjaan

### Tujuan
Memporting Gmvault dari Python 2.7 ke Python 3.11+ sehingga dapat:
- ✅ Dijalankan dengan Python 3.11+
- ✅ Terkoneksi ke Gmail melalui IMAP dengan OAuth2
- ✅ Melakukan backup (sync) email dari Gmail ke lokal
- ✅ Melakukan restore email dari lokal ke Gmail
- ✅ Export email ke format standar
- ✅ Semua dependency kompatibel dan update-to-date

### Yang TIDAK termasuk dalam scope
- ❌ Perubahan arsitektur besar (misal: mengganti database)
- ❌ Fitur baru di luar fungsionalitas existing
- ❌ GUI/web interface
- ❌ Dukungan multi-threading/async

---

## 2. Tahapan Pekerjaan

### Fase 1: Persiapan & Tooling (3-5 hari)

- [x] **1.1** Analisis kode existing (SELESAI)
- [x] **1.2** Setup environment Python 3.11+ (SUDAH ADA)
- [x] **1.3** Install `2to3` (SUDAH ADA DI STANDARD LIBRARY)
- [x] **1.4** Setup virtual environment (`python -m venv venv`)
- [x] **1.5** Setup testing framework (`pytest` + `pytest-cov`)
- [x] **1.6** Setup CI/CD (GitHub Actions) untuk test otomatis (`.github/workflows/ci.yml`)
- [x] **1.7** Buat `pyproject.toml` untuk build sistem modern
- [x] **1.8** Git init + branch `python3-porting` + push ke `https://github.com/raw-dani/GMvault.git`

### Fase 2: Automated Porting dengan 2to3 (2-3 hari)

- [x] **2.1** Jalankan `2to3` pada seluruh source di `src/` (45 file)
- [x] **2.2** Jalankan `2to3` pada file-file test
- [x] **2.3** Review dan fix hasil konversi otomatis
- [x] **2.4** Fix manual syntax yang tidak tertangani `2to3`:
  - `except Exception, e:` → `except Exception as e:` (tidak ditemukan, sudah bersih)
  - `raise Exception, "msg"` → `raise Exception("msg")` (tidak ditemukan)
  - `print >> sys.stderr, x` → `print(x, file=sys.stderr)` (tidak ditemukan)
  - `backtick` syntax `` `x` `` → `repr(x)` (hanya di docstring, aman)
  - Fix `TabError`/`IndentationError` di `src/sandbox/unicode_test.py`
  - Fix `long()` → `int()` di `src/sandbox/common_gmvault.py`
- [x] **2.5** Verify tidak ada syntax error (`python -m py_compile` → semua lolos)

### Fase 3: Update Dependencies (3-5 hari)

- [x] **3.1** Update `IMAPClient` 0.13 → 3.x (terpasang `imapclient==3.1.0`):
  - [x] Pelajari API changes antara 0.13 dan 3.x
  - [x] Update `mod_imap.py` (MonkeyIMAPClient): ganti `imapclient.six.binary_type/text_type` → `bytes`/`str` (six dihapus di 3.x)
  - [x] Update signature `MonkeyIMAPClient.__init__`: `need_ssl` → `ssl` (sesuai `IMAPClient.__init__(host, port, use_uid, ssl, ...)`)
  - [x] Update call site `imap_utils.py:290` (`need_ssl=` → `ssl=`)
  - [x] Monkey-patching `_convert_INTERNALDATE` & `imaplib.Commands['COMPRESS']` tetap valid di 3.1.0
  - [~] Update mendalam `imap_utils.py` (GIMAPFetcher) → lanjut di Fase 6 (IMAP & Jaringan)
   
- [x] **3.2** Update/Ganti `Logbook` 0.10.1 → `loguru` (`loguru==0.7.3`):
  - [x] Tulis ulang `log_utils.py` dengan backend `loguru`, pertahankan interface `LoggerFactory` (get_logger + setup_cli_app_handler/setup_simple_*)
  - [x] Hapus import `logbook`; default handler di-remove agar senyap sampai setup dipanggil (mirip NullHandler)
   
- [x] **3.3** Update `chardet` 2.3.0 → 5.x (`chardet==5.2.0`):
  - [x] `chardet.detect()` API identik, tidak ada perubahan kode (`gmvault_utils.py:522`, sandbox)
   
- [x] **3.4** `argparse` sudah built-in di Python 3 → tidak perlu dependency eksternal (tidak ada di `pyproject.toml`)

- [ ] **3.5** Hapus custom `Conf` helper, ganti `configparser` — **DITUNDA**: `gmv.conf.conf_helper` sudah kompatibel Python 3 (ter-impor bersih). Mengganti ke `configparser` mengubah format file `.conf` gmvault dan berisiko tinggi tanpa manfaat porting → dilanjut di refactor terpisah jika diperlukan.

### Fase 4: Perubahan Inti Python 2 → 3 (5-7 hari)

#### 4.1 String & Encoding
- [x] Ganti semua `unicode()` → `str()` (sudah otomatis oleh 2to3 di Fase 2; tidak ada `unicode()` tersisa di kode)
- [x] Ganti `basestring` → `str` (tidak ada referensi `basestring` tersisa)
- [x] Perbaiki encoding/decoding di `gmvault_utils.py`: modernisasi guard `type(x) == type(str())` → `isinstance(x, str)` (guess_encoding:506, convert_argv_to_unicode:566)
- [x] Update fungsi `convert_to_unicode()`, `guess_encoding()`, `convert_argv_to_unicode()`: sudah benar setelah 2to3 (`str(bytes, enc)` = decode di Py3); teruji dengan input bytes
- [x] Update fungsi `utf7_encode`/`utf7_decode` di `imap_utils.py`:
  - [x] `utf7_modified_base64`: hasil `.encode('utf-7')` (bytes di Py3) di-decode kembali ke `str` agar `''.join` tidak gagal
  - [x] `utf7_modified_unbase64`: gunakan `codecs.decode(s.encode('ascii'), 'utf-7')` (str tidak punya `.decode()` di Py3)
  - [x] `utf7_encode`: guard diubah — tolak input `bytes`, izinkan `str` non-ASCII (itu yang memang di-encode)
  - [x] Round-trip ASCII & non-ASCII (Café, Répertoire, Boîte de réception) teruji `PASS`

#### 4.2 I/O & Files
- [x] Ganti `StringIO.StringIO` → `io.StringIO` (sudah otomatis oleh 2to3; tersisa hanya di komentar)
- [x] Ganti `cStringIO.StringIO` → `io.BytesIO`:
  - [x] `mod_imap.py` (read/new_read/readline): socket membaca `bytes` → `io.StringIO` diganti `io.BytesIO` agar `chunks.write(bytes)` & `getvalue()` tidak gagal
  - [x] `readline`: fix comparasi `char in ("\n","")` → `char in (b"\n", b"")` (bytes vs str, hindari infinite loop)
- [x] `os.tempnam` → `tempfile`: tidak ada pemakaian `os.tempnam` di source (tidak perlu diubah)
- [x] Update file operations bytes vs string:
  - [x] `gmvault_db.py` `_get_data_file_from_id`: data file dibuka `'rb'` (gzip & plain) agar `decryptCTR(f.read())` & konten email kembali sebagai `bytes` (konsisten dg write path `'wb'`)
  - [x] `io.StringIO` di `gmvault_utils.py` (traceback buffer) & `struct_parser.py` (tokenizer) sudah benar menampung `str` → tidak diubah
  - [x] Komentar `StringIO.StringIO` di `gmvault_db.py` diperbarui ke `io.BytesIO()`

#### 4.3 Collections & Iteration
- [x] Ganti `dict.iteritems()` → `dict.items()` (sudah otomatis 2to3; tidak ada sisa di source)
- [x] Ganti `dict.iterkeys()` → `dict.keys()` (sudah otomatis 2to3; tidak ada sisa di source)
- [x] Ganti `itertools.izip_longest` → `itertools.zip_longest` (sudah otomatis 2to3; tidak ada sisa)
- [x] Ganti `itertools.ifilter` → `builtins.filter` (sudah otomatis 2to3; tidak ada sisa)
- [x] Ganti `xrange` → `range` (sudah otomatis 2to3; tidak ada sisa — termasuk `sandbox/common_gmvault.py`)
- [x] Update `cmp_to_key` → `functools.cmp_to_key`: hapus redefinisi lokal di `gmvault_utils.py` (line 303), impor `from functools import cmp_to_key`; `get_all_dirs_posterior_to` teruji `PASS`

#### 4.4 Network & HTTP
- [x] Ganti `urllib2` → `urllib.request` + `urllib.error` (sudah otomatis 2to3; import di `credential_utils.py`, `gmvault_utils.py`, `oauth2*.py` sudah benar)
- [x] Ganti `urllib.urlencode` → `urllib.parse.urlencode` (sudah otomatis 2to3)
- [x] Ganti `urllib.quote` → `urllib.parse.quote` (`gmvault_utils.py`, `oauth2.py`, `oauth2_runner.py` sudah benar)
- [x] Update `credential_utils.py` untuk HTTP requests: fix bug Py3 pada `urlopen` — data POST harus `bytes` + header `Content-Type: application/x-www-form-urlencoded` (pakai `urllib.request.Request`). Diterapkan di `_get_oauth2_acc_tok_from_ref_tok` & `_get_authorization_tokens`
- [x] Update `gmvault_utils.py` untuk URL handling: `escape_url`/`unescape_url` sudah pakai `urllib.parse.quote`/`unquote` (teruji round-trip)
- [x] Sama untuk sandbox `oauth2.py` & `oauth2_runner.py` (pola `urlopen(url, urlencode(params))` → `Request` dengan bytes data)

#### 4.5 Miscellaneous
- [x] Ganti `raw_input()` → `input()` (sudah otomatis 2to3; tidak ada `raw_input` tersisa)
- [x] Ganti `long` type → `int` (sudah otomatis 2to3; tidak ada `long(` tersisa — termasuk `sandbox/common_gmvault.py`)
- [x] Update `__getslice__` → `__getitem__` (tidak ada penggunaan `__getslice__` di source)
- [x] Update `has_key()` → `in` operator (tidak ada `.has_key(` tersisa)
- [x] Update `sort` dengan `cmp` → `sort` dengan `key`/`cmp_to_key` (tidak ada `.sort(cmp=...)` tersisa)
- [x] Fix `map()` iterator: 3 pemakaian (`collections_utils.py:76`, `imap_utils.py:652`, `gmvault_db.py:519`) semuanya di-feed ke `join()`/`fnmatch.filter()` yang menerima iterable → tidak perlu `list()`
- [x] Fix `filter()` iterator: hanya `fnmatch.filter()` (mengembalikan list) → aman
- [x] Update `type()` comparison: tidak ada `type(a) == type(b)` di kode inti; satu-satunya di `sandbox/unicode_test.py:14` (`type(a_str) != type('a')`) sudah benar secara semantik di Py3 (ekuivalen `isinstance(a_str, str)`)
- [x] Negative scan komprehensif: tidak ada idiom Py2 (raw_input/long/__getslice__/has_key__/xrange/unicode()/sort cmp) tersisa; `compileall` lolos (exit 0)

### Fase 5: Perbaikan Autentikasi OAuth2 (3-4 hari)

- [ ] **5.1** Register aplikasi baru di Google Cloud Console **(MANUAL — dilakukan user)**:
  - [ ] Buat project baru
  - [ ] Enable Gmail API
  - [ ] Buat OAuth 2.0 Client ID (Desktop application)
  - [ ] Catat Client ID dan Client Secret baru
  - [x] Infra kode sudah siap (approach **env var**): kredensial dibaca dari `GMVAULT_CLIENT_ID` / `GMVAULT_CLIENT_SECRET` (`credential_utils.py`: `get_oauth2_credentials()`/`get_oauth2_client_id()`/`get_oauth2_client_secret()`), hardcoded credential dihapus dari `gmvault_const.py:80-81` dan fallback di `credential_utils.py` (254-255, 295-296)
  
- [ ] **5.2** Update hardcoded credentials di `gmvault_const.py`:
  - [ ] Ganti `1070918343777-...` dengan Client ID baru
  - [ ] Ganti `IVkl_pglv5cX...` dengan Client Secret baru
  
- [x] **5.3** Update `credential_utils.py`:
  - [x] Ganti `urllib2` → `requests` library: `urllib2` sudah tidak ada di core (0 occ, dikonversi 2to3 + fix 4.4); token-exchange `_get_oauth2_acc_tok_from_ref_tok` & `_get_authorization_tokens` ditulis ulang pakai `requests.post` (import `requests` ditambah, import `urllib` yang tak terpakai dibuang)
  - [x] Update OAuth2 token refresh flow: logika `refresh_token` grant dipertahankan, dipusatkan ke helper `_post_token_request(params)`
  - [x] Handle error responses dari Google: `_post_token_request` menangkap `requests.exceptions.RequestException`, respons non-JSON, dan payload `{"error": ...}` → raise pesan jelas (`Google oauth2 error: invalid_grant ...`) instead of `KeyError`. Teruji.
  - [~] CATATAN: `redirect_uri` masih `urn:ietf:wg:oauth:2.0:oob` (deprecated Google) — tahap consent mungkin gagal; perlu migrasi ke loopback (`http://127.0.0.1:PORT`) agar end-to-end berfungsi (lihat 5.4).

- [x] **5.4** Verify OAuth2 flow end-to-end:
  - [x] Test authorization URL generation: `generate_permission_url()` menghasilkan URL dengan `client_id`/`response_type=code`/`scope`/`redirect_uri` (teruji via `src/sandbox/verify_oauth2.py`)
  - [x] Test XOAUTH2 IMAP authentication (offline): fix 2 bug Py3 kritis di `_generate_oauth2_auth_string`:
        - `'\1'` → `'\x01'` (separator kontrol SASL yang benar; sebelumnya literal backslash-1)
        - `base64.b64encode(str)` → `base64.b64encode(auth_string.encode('utf-8'))` (Py3 butuh bytes; sebelumnya `TypeError`)
        - teruji: raw string ber-`\x01`, base64 kembalian `bytes` dan round-trip
  - [x] Migrasi dari deprecated `oob` → **loopback**: `gmvault_const.py` default `redirect_uri=http://127.0.0.1:8080`; tambah `_is_loopback()` + `_capture_oauth_code()` (lokal HTTP server menangkap `code`); `_get_oauth2_tokens` otomatis pakai loopback, hapus `eval(input(...))` yang tidak aman
  - [x] Test loopback capture server: teruji menangkap `?code=` (simulasi redirect Google)
  - [~] Test access token acquisition & refresh token (LIVE): butuh akun Google + `GMVAULT_CLIENT_ID`/`GMVAULT_CLIENT_SECRET` + daftarkan `http://127.0.0.1:8080` sbg Authorized redirect URI. Jalankan: `python src/sandbox/verify_oauth2.py --live you@gmail.com`. Token-exchange logic (`requests`) & error handling sudah teruji (5.3).
  - [x] Tambah `src/sandbox/verify_oauth2.py` untuk verifikasi (offline + live)

### Fase 6: Perbaikan IMAP & Jaringan (3-5 hari)

- [x] **6.1** Update `mod_imap.py`:
  - [x] Update `MonkeyIMAPClient` untuk IMAPClient 3.x
  - [x] Update `IMAP4COMPSSL` untuk Python 3 `ssl` module
  - [x] Perbaiki monkey-patching `_convert_INTERNALDATE`
  - [x] Update compression (DEFLATE) implementasi
  - [x] Update socket timeout handling
  - [x] Update `read()` dan `readline()` untuk bytes handling

- [ ] **6.2** Update `imap_utils.py`:
  - [ ] Update `GIMAPFetcher` class
  - [ ] Update `retry` decorator untuk Python 3
  - [ ] Update IMAP search/fetch methods
  - [ ] Update label operations
  - [ ] Update push/restore operations

- [ ] **6.3** Implementasi rate limiting & exponential backoff:
  - [ ] Tambah delay antar request batch
  - [ ] Handle Gmail rate limiting response
  - [ ] Implementasi smart reconnect strategy

### Fase 7: Update Gmvault Core (3-4 hari)

- [ ] **7.1** Update `gmvault.py`:
  - [ ] Fix `GMVaulter` class untuk Python 3
  - [ ] Update `IMAPBatchFetcher`
  - [ ] Update sync operations (`_sync_emails`, `_sync_chats`)
  - [ ] Update restore operations (`restore_emails`, `restore_chats`)
  - [ ] Update `check_clean_db` dan `_delete_sync`
  
- [ ] **7.2** Update `gmvault_db.py`:
  - [ ] Fix `GmailStorer` untuk Python 3
  - [ ] Update file I/O (bytes vs string)
  - [ ] Update JSON serialization
  - [ ] Update gzip compression
  - [ ] Update enkripsi Blowfish → AES (atau ganti dengan `cryptography` library)

- [ ] **7.3** Update `gmvault_export.py`:
  - [ ] Fix export functionality untuk Python 3

- [ ] **7.4** Update `gmv_cmd.py`:
  - [ ] Fix CLI parser (`argparse` → API yang baru)
  - [ ] Update command handlers
  - [ ] Fix signal handling

### Fase 8: Testing (3-5 hari)

- [ ] **8.1** Update test infrastructure:
  - [ ] Update `gmvault_tests.py` untuk Python 3
  - [ ] Update `gmv_cmd_tests.py` untuk Python 3
  - [ ] Update `validation_tests.py` untuk Python 3
  - [ ] Update `gmvault_essential_tests.py` untuk Python 3
  
- [ ] **8.2** Mock Gmail IMAP server untuk unit test:
  - [ ] Buat mock IMAP server menggunakan `aiosmtpd` atau custom mock
  - [ ] Mock OAuth2 endpoints
  
- [ ] **8.3** Integration test:
  - [ ] Buat test Gmail account untuk integration test
  - [ ] Test backup flow end-to-end
  - [ ] Test restore flow end-to-end
  
- [ ] **8.4** Manual testing:
  - [ ] Test dengan berbagai ukuran mailbox
  - [ ] Test resume/crash recovery
  - [ ] Test error scenarios

### Fase 9: Build & Packaging (2-3 hari)

- [ ] **9.1** Update `setup.py` → `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=68.0", "wheel"]
  build-backend = "setuptools.backends._legacy:_Backend"

  [project]
  name = "gmvault"
  version = "2.0.0"
  requires-python = ">=3.9"
  dependencies = [
      "imapclient>=3.0.0",
      "chardet>=5.0,<6.0",
      "requests>=2.28.0",
      "cryptography>=39.0.0",
      "loguru>=0.7.0",
  ]
  ```

- [ ] **9.2** Update script entry points
- [ ] **9.3** Update MANIFEST.in
- [ ] **9.4** Update README.md (install instructions, Python 3 info)
- [ ] **9.5** Update Makefile
- [ ] **9.6** Test install dari source (`pip install .`)
- [ ] **9.7** Test install dari PyPI (`pip install gmvault`)

### Fase 10: Dokumentasi & Rilis (2-3 hari)

- [ ] **10.1** Update dokumentasi instalasi
- [ ] **10.2** Update dokumentasi OAuth2 setup
- [ ] **10.3** Buat CHANGELOG.md
- [ ] **10.4** Buat RELEASE-NOTE.txt untuk v2.0.0
- [ ] **10.5** Update AUTHORS.md
- [ ] **10.6** Push ke PyPI
- [ ] **10.7** Buat GitHub Release

---

## 3. Rincian Perubahan Per File

### 3.1 `src/gmv/mod_imap.py` (High Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 27 | `import cStringIO` → `import io` | Modul dihapus di Python 3 |
| 32 | `import imapclient` | Update API untuk IMAPClient 3.x |
| 51-77 | `mod_convert_INTERNALDATE` | Fix regex dan tzinfo handling |
| 80 | Monkey-patch | Update path untuk IMAPClient 3.x |
| 105-217 | `IMAP4COMPSSL` class | Rewrite untuk Python 3 `ssl` + `sock` API |
| 238-345 | `MonkeyIMAPClient` class | Update untuk IMAPClient 3.x API |
| 256 | `oauth2_login` | String handling fix |
| 260-299 | `search` method | Bytes/string fix |
| 301-328 | `append` method | Timedate dan bytes fix |
| 330-343 | `enable_compression` | Update untuk Python 3 |

### 3.2 `src/gmv/imap_utils.py` (High Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 72-193 | `retry` decorator | Fix closure dan exception handling |
| 248-522 | `GIMAPFetcher` class | String/bytes di seluruh method |
| 546-628 | `create_gmail_labels` | Fix encoding |
| 654, 662 | `_imap.uid('STORE', ...)` | Bytes arguments |
| 780-826 | `push_data` | Bytes body fix |
| 896-970 | `decode_labels`, `utf7_*` | Unicode/bytes fix |

### 3.3 `src/gmv/credential_utils.py` (High Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 26-27 | `import urllib` → `import urllib.parse`, `import urllib.request` | Urllib restruktur |
| 64-163 | `CredentialHelper` class | OAuth2 flow update |
| 240-273 | `_get_oauth2_acc_tok_from_ref_tok` | HTTP request → `requests` library |
| 275-308 | `_get_authorization_tokens` | HTTP request → `requests` library |
| 363-366 | `_generate_oauth2_auth_string` | Bytes encoding fix |

### 3.4 `src/gmv/gmvault_utils.py` (Medium Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 29 | `import StringIO` → `import io` | StringIO |
| 34 | `import urllib` → `import urllib.parse` | Urllib |
| 104-121 | `get_exception_traceback` | I/O fix |
| 496-528 | `guess_encoding` | Type check fix (unicode type) |
| 531-558 | `convert_to_unicode` | Rewrite untuk str/bytes |
| 560-596 | `convert_argv_to_unicode` | Rewrite untuk Python 3 |
| 698-701 | `chunker` | `xrange` → `range` |
| 704-730 | URL helper functions | `urllib.quote` → `urllib.parse.quote` |

### 3.5 `src/gmv/gmvault.py` (Medium Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| Seluruh file | Exception syntax | `except Exception, e:` → `except Exception as e:` |
| 666 | `itertools.izip_longest` | → `itertools.zip_longest` |
| 959, 1095 | `itertools.izip_longest` | → `itertools.zip_longest` |
| 675 | Set comprehension | Python 2.6 → Python 3 syntax |

### 3.6 `src/gmv/gmvault_db.py` (Medium Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 28 | `import StringIO` | → `import io` |
| 28 | `import codecs` | Mungkin tidak perlu lagi |
| Fungsi enkripsi | Blowfish → AES | Ganti dengan `cryptography` library |
| Fungsi file I/O | Bytes/string fix | Di seluruh fungsi |

### 3.7 `src/gmv/gmvault_const.py` (Low Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 80-81 | OAuth2 credentials | Update dengan Client ID/Secret baru |
| 35-88 | Default config | Minor update (mungkin tidak perlu) |

### 3.8 `src/gmv/gmv_cmd.py` (Medium Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| 25 | `import signal` | Signal handling fix |
| 27 | `import argparse` | Sudah built-in, tidak masalah |
| Kode handler | Exception handling | Fix syntax di seluruh handler |

### 3.9 `src/gmv/gmvault_export.py` (Medium Priority)
| Baris | Perubahan | Keterangan |
|---|---|---|
| Seluruh file | Python 2→3 fixes | Apply 2to3 + manual fixes |

### 3.10 Test Files (Medium Priority)
| File | Perubahan |
|---|---|
| `src/gmvault_tests.py` | Python 2→3 syntax, update assertions |
| `src/gmv_cmd_tests.py` | Python 2→3 syntax |
| `src/gmvault_essential_tests.py` | Python 2→3 syntax |
| `src/validation_tests.py` | Python 2→3 syntax |
| `src/sandbox_tests.py` | Python 2→3 syntax |

---

## 4. Dependency Updates

### Dependency Baru (`pyproject.toml`)

```toml
[project]
dependencies = [
    "imapclient>=3.0.0,<4.0.0",    # IMAP client (update dari 0.13)
    "chardet>=5.0.0,<6.0.0",       # Character encoding detection
    "requests>=2.28.0,<3.0.0",     # HTTP client (ganti urllib2)
    "cryptography>=41.0.0,<42.0.0",# Enkripsi modern (ganti blowfish)
    "loguru>=0.7.0,<1.0.0",        # Logging (ganti Logbook)
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "flake8>=6.0",
    "black>=23.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
]
```

### Perbandingan Dependency

| Library | Versi Lama | Versi Baru | Alasan Perubahan |
|---|---|---|---|
| IMAPClient | 0.13 | 3.x | API break, bug fixes, Python 3 support |
| Logbook | 0.10.1 | **Dihapus** | Tidak kompatibel Python 3.11 |
| **Loguru** (baru) | - | 0.7+ | Logging modern, aktif di-maintain |
| chardet | 2.3.0 | 5.x | Update minor |
| argparse | Eksternal | **Dihapus** | Built-in sejak Python 3.2 |
| **requests** (baru) | - | 2.28+ | Ganti urllib2 yang deprecated |
| **cryptography** (baru) | - | 41+ | Ganti blowfish.py custom |
| pyOpenSSL (opsional) | - | 23+ | Untuk TLS modern |

---

## 5. Perubahan Autentikasi OAuth2

### Alur Baru

```
User runs: gmvault sync user@gmail.com

1. Cek file ~/.gmvault/user@gmail.com.oauth2
   ↓ (tidak ada / expired)
2. Generate authorization URL:
   https://accounts.google.com/o/oauth2/v2/auth?...
   ↓
3. Buka browser untuk user grant access
   ↓
4. Dapatkan authorization code
   ↓
5. Tukar dengan access token + refresh token (via requests library)
   POST https://oauth2.googleapis.com/token
   ↓
6. Simpan token di ~/.gmvault/user@gmail.com.oauth2
   ↓
7. Generate XOAUTH2 auth string:
   user=user@gmail.com\1auth=Bearer {access_token}\1\1
   ↓
8. Authenticate ke IMAP via XOAUTH2
```

### Yang Perlu Diubah

1. **Google Cloud Console**:
   - Buat project baru
   - Enable Gmail API
   - Buat OAuth 2.0 Client ID (type: Desktop app)
   - Download credentials JSON

2. **Update gmvault_const.py**:
   - Client ID baru
   - Client Secret baru

3. **Update credential_utils.py**:
   - Endpoint OAuth baru: `/o/oauth2/v2/auth` → `/o/oauth2/auth` masih valid
   - Token endpoint: `/o/oauth2/token` → `/o/oauth2/token` masih valid
   - Tapi sebaiknya gunakan endpoint baru: `https://oauth2.googleapis.com/token`
   - Gunakan `requests.Session()` untuk retry/backoff

4. **Keamanan**:
   - Hapus hardcoded credential dari source code
   - Gunakan environment variable: `GMVAULT_CLIENT_ID`, `GMVAULT_CLIENT_SECRET`
   - Atau simpan dalam file konfigurasi
   - Atau bundle credentials dengan fallback ke user-provided

---

## 6. Perubahan IMAP & Jaringan

### IMAPClient 0.13 → 3.x API Changes

| 0.13 API | 3.x API | Notes |
|---|---|---|
| `search('ALL')` | `search('ALL')` | Masih sama |
| `fetch(ids, attrs)` | `fetch(ids, attrs)` | Return type berbeda |
| `select_folder(folder)` | `select_folder(folder)` | Sama |
| `append(folder, msg, flags, time)` | `append(folder, msg, flags, time)` | Sama |
| `logout()` | `logout()` | Sama |
| `xlist_folders()` | `list_folders()` | `XLIST` deprecated, gunakan `LIST` |
| `folder_exists(folder)` | `folder_exists(folder)` | Sama |
| `create_folder(folder)` | `create_folder(folder)` | Sama |

### SSL/TLS Modern

**Custom IMAP4COMPSSL** → **Gunakan built-in IMAPClient SSL**:

```python
# Before (Python 2)
server = IMAP4COMPSSL(host, port)

# After (Python 3)
import ssl
context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED

# Biarkan IMAPClient handle SSL
server = IMAPClient(host, port=port, ssl=True, ssl_context=context)
```

### Rate Limiting

```python
# Tambahkan delay antar batch request
import time
import random

def rate_limited_request(func):
    def wrapper(*args, **kwargs):
        time.sleep(random.uniform(0.5, 2.0))  # Random delay 0.5-2s
        return func(*args, **kwargs)
    return wrapper
```

---

## 7. Perubahan Storage & Enkripsi

### Enkripsi: Blowfish → AES-GCM

**Sebelumnya (Blowfish - custom, tidak aman):**
```python
from gmv.blowfish import Blowfish
cipher = Blowfish(secret_key)
cipher.initCTR()
encrypted = cipher.encryptCTR(data)
```

**Sesudah (AES-256-GCM - modern, aman):**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Generate key dari password
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,
)
key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
cipher = Fernet(key)
encrypted = cipher.encrypt(data.encode())
```

### Format File Storage (Tetap Sama)

| File | Format | Content |
|---|---|---|
| `YYYY-MM/msg_id.eml` | Plain/Gzip | Raw email (RFC 2822) |
| `YYYY-MM/msg_id.meta` | JSON | Metadata (labels, flags, dates) |
| `.info/token.sec` | AES encrypted | Storage encryption key |
| `.info/.owner_account.info` | JSON | List of account owners |

---

## 8. Testing Strategy

### Unit Tests (Offline - Mock Gmail)

| Test | Coverage | Tools |
|---|---|---|
| OAuth2 credential management | `CredentialHelper` | `pytest`, `unittest.mock` |
| IMAP command formatting | `GIMAPFetcher` methods | `pytest`, mock IMAP server |
| Error handling & retry | `retry` decorator | `pytest`, mock exceptions |
| Database operations | `GmailStorer` | `pytest`, temp directory |
| Config parsing | `Conf` class | `pytest`, temp config files |
| Encoding/Decoding | UTF7, charset | `pytest` |

### Integration Tests (With Real Gmail Account)

| Test | Description |
|---|---|
| `test_oauth2_flow` | Test OAuth2 authentication end-to-end |
| `test_imap_connection` | Test IMAP connect, search, fetch |
| `test_sync_small` | Test sync 5-10 emails |
| `test_restore_small` | Test restore 5-10 emails |
| `test_resume_sync` | Test resume after interruption |
| `test_encryption` | Test encrypt/decrypt cycle |

### Performance Tests

| Test | Description | Target |
|---|---|---|
| `test_sync_1000` | Sync 1000 emails | < 5 menit |
| `test_restore_100` | Restore 100 emails | < 2 menit |
| `test_concurrent_connections` | Multiple sync sessions | Tidak crash |

---

## 9. Risiko & Mitigasi

| Risiko | Dampak | Probabilitas | Mitigasi |
|---|---|---|---|
| **IMAPClient 3.x API tidak backward compatible** | Tinggi - banyak kode perlu diubah | Tinggi | Buat adapter/wrapper layer |
| **Google block OAuth2 credential** | Tinggi - aplikasi tidak bisa login | Sedang | Register aplikasi baru di Google Cloud |
| **Gmail rate limiting untuk backup massal** | Sedang - sync lambat/gagal | Sedang | Implementasi exponential backoff + user notification |
| **Custom enkripsi Blowfish data tidak bisa didekripsi** | Tinggi - data lama tidak terbaca | Rendah | Buat migration tool: decrypt Blowfish → re-encrypt AES |
| **Encoding issues dengan email non-ASCII** | Sedang - beberapa email corrupt | Sedang | Extensive testing dengan berbagai charset |
| **Performa menurun dibanding Python 2** | Rendah - backup lebih lambat | Sedang | Profiling, optimasi batch sizes |
| **SSL/TLS compatibility issues** | Tinggi - tidak bisa connect | Rendah | Test dengan berbagai Python/OpenSSL version |

### Data Migration Plan

Untuk user yang sudah memiliki data backup dengan enkripsi Blowfish:

```bash
# Tool migrasi enkripsi
gmvault migrate --old-db ~/gmvault-db --new-db ~/gmvault-db-v2

# Atau migrasi in-place
gmvault migrate --in-place ~/gmvault-db
```

---

## 10. Roadmap Timeline

```
Minggu 1-2: Fase 1-3 (Persiapan + Automated Porting + Dependencies)
  Hari 1-3:  Setup environment, 2to3 conversion
  Hari 4-7:  Update IMAPClient 3.x
  Hari 8-10: Update Logbook/Loguru, chardet, requests

Minggu 3-4: Fase 4-5 (Core Python 3 fixes + OAuth2)
  Hari 11-14: String/encoding fixes (gmvault_utils.py, imap_utils.py)
  Hari 15-18: Collection/iteration fixes (gmvault.py, gmvault_db.py)
  Hari 19-21: Network/IO fixes (credential_utils.py, gmv_cmd.py)
  Hari 22-24: OAuth2 registration + credential_utils.py rewrite

Minggu 5-6: Fase 6-8 (IMAP fixes + Core fixes + Testing)
  Hari 25-28: IMAP rewrites (mod_imap.py, imap_utils.py)
  Hari 29-32: Core class fixes (gmvault.py, gmvault_db.py)
  Hari 33-36: Encryption migration (Blowfish → AES)
  Hari 37-40: Testing (unit + integration + performance)

Minggu 7: Fase 9-10 (Build + Dokumentasi + Rilis)
  Hari 41-43: pyproject.toml, packaging, docs
  Hari 44-45: Final testing, release
```

### Milestones

| Milestone | Target | Deliverable |
|---|---|---|
| M1 | Hari 10 | Kode ter-kompilasi di Python 3.11 (masih error runtime) |
| M2 | Hari 24 | OAuth2 flow berfungsi, bisa connect ke Gmail |
| M3 | Hari 35 | Sync & restore berfungsi untuk email sederhana |
| M4 | Hari 40 | Test suite passing, termasuk integration test |
| M5 | Hari 45 | Rilis v2.0.0rc1 ke PyPI |

---

## 11. Referensi

### Dokumentasi Google
- [Gmail IMAP Extensions](https://developers.google.com/gmail/imap/imap-extensions)
- [OAuth 2.0 for Installed Applications](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Scopes](https://developers.google.com/identity/protocols/oauth2/scopes#gmail)
- [Register OAuth Client](https://console.cloud.google.com/apis/credentials)

### Python Porting Guide
- [Python 3 Porting Guide (Official)](https://docs.python.org/3/howto/pyporting.html)
- [Cheat Sheet: Python 2 vs Python 3](https://pythoncheatsheet.org/blog/python2-vs-python3)
- [2to3 Automated Python 2 to 3 Code Translation](https://docs.python.org/3/library/2to3.html)

### Libraries
- [IMAPClient 3.x Documentation](https://imapclient.readthedocs.io/)
- [Cryptography (Fernet/AES) Documentation](https://cryptography.io/en/latest/fernet/)
- [Requests Library Documentation](https://requests.readthedocs.io/)
- [Loguru Documentation](https://loguru.readthedocs.io/)

### Related Projects
- [got-your-back (gyb)](https://github.com/GYBFramework/gyb) - Alternative Gmail backup tool
- [OfflineIMAP](https://github.com/OfflineIMAP/offlineimap) - IMAP sync tool
- [mbsync/isync](https://isync.sourceforge.io/) - IMAP sync (actively maintained)