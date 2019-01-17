"""
Tests configuration
"""
import sys
import string
import random
from pathlib import Path

import pytest

import prolix

# path to the test directory
TEST_PATH = Path(__file__).parent
# path to the package directory
PKG_PATH = TEST_PATH.parent


# add module path to sys path
sys.path.insert(0, str(PKG_PATH))


@pytest.fixture
def user() -> prolix.User:
    """ Create a test user profile, delete when finished. """
    name = ''.join([random.choice(string.ascii_lowercase) for _ in range(5)])
    current_user = prolix.User()
    user = prolix.User(name, is_current_user=True)
    yield user
    # delete test user and set current user back
    user.delete_user()
    current_user.is_current_user = True
