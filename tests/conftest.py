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
def user():
    """ Create a test user profile, delete when finished. """
    name = ''.join([random.choice(string.ascii_lowercase) for x in range(5)])
    prolix.create_user(name)
    yield name
    prolix.delete_user(name)




