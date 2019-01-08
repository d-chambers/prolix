"""
Tests configuration
"""
import sys
from pathlib import Path

import pytest

# path to the test directory
TEST_PATH = Path(__file__).parent
# path to the package directory
PKG_PATH = TEST_PATH.parent


# add module path to sys path
sys.path.insert(0, str(PKG_PATH))


def pytest_namespace():
    """ add the expected files to the py.test namespace """
    odict = {
        "test_path": TEST_PATH,
        "package_path": PKG_PATH,
    }
    return odict
