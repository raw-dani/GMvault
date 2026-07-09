"""
Smoke test for the Python 3 port: ensure every gmv module imports cleanly
under the running interpreter. This validates the 2to3 + manual porting work
without requiring a live Gmail account or network access.

Run with:  pytest -o python_files="*_smoke_tests.py"
"""
import importlib
import os
import sys

import pytest

# make sure the src layout is importable when run from the repo root
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

PKG = "gmv"
MODULES = [
    "gmv.log_utils",
    "gmv.conf.exceptions",
    "gmv.conf.conf_helper",
    "gmv.conf.utils.struct_parser",
    "gmv.blowfish",
    "gmv.collections_utils",
    "gmv.gmvault_const",
    "gmv.gmvault_utils",
    "gmv.cmdline_utils",
    "gmv.credential_utils",
    "gmv.mod_imap",
    "gmv.imap_utils",
    "gmv.gmvault_db",
    "gmv.gmvault_export",
    "gmv.gmvault",
    "gmv.gmv_cmd",
]


@pytest.mark.parametrize("modname", MODULES)
def test_module_imports(modname):
    importlib.import_module(modname)


def test_package_importable():
    importlib.import_module(PKG)
