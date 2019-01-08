"""
Tests for core of prolix
"""
from pathlib import Path

import pandas as pd
import pytest

import prolix


@pytest.fixture(scope='session')
def economist_gre_words_path():
    """ return the path to the economist word file. """
    return Path(prolix.__path__[0]) / 'data' / 'economist_gre_words.txt'


@pytest.fixture(scope='session')
def words_text_path():
    """ return the path to the words.txt file. """
    return Path(prolix.__path__[0]) / 'data' / 'words.txt'


@pytest.fixture(scope='session')
def populated_word_db(words_text_path, economist_gre_words_path):
    """ Populate the word db, return df """
    words1 = prolix.store._read_economist_words(economist_gre_words_path)
    words2 = prolix.store._read_textlist(words_text_path)
    prolix.add_words(words1 + words2)
    return prolix.read_words()


def test_word_df(populated_word_db):
    df = populated_word_db
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns).issuperset({'definition'}), 'words must have definition'
