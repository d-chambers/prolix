"""
Tests for user features
"""

import numpy as np
import pytest

import pandas as pd
import peewee

import prolix



user_who_doesnt_exist = 'bob_the_guy_who_cant_be_in_the_database'


@pytest.fixture
def random_words():
    """ Get a list of 5 random words """
    df = prolix.read_words()
    return list(np.random.choice(df.index.values, 5))


class TestDiscardedWords:
    """ tests for discarding words """


    @pytest.fixture
    def user_dwords(self, user, random_words):
        """ Create a user, discard some words """
        prolix.user.discard_word(random_words)
        return user

    def test_discarded_words_recorded(self, user_dwords, random_words):
        """ Ensure the discarded words are recorded and returned """
        words = prolix.user.get_discarded_words(user=user_dwords)
        assert set(words) == set(random_words)


class TestUserAnswerTable:
    """ Test getting a df of how the user has answered the words. """

    @pytest.fixture
    def correctly_answered_df(self, user, random_words):
        """ DF of a user who has correctly answered some words. """
        prolix.user._correctly_answered_word(random_words)
        return prolix.user._correctly_answered_word(random_words, user=user)

    def test_non_existent_user(self):
        """ ensure the database is still populated """
        df = prolix.user._get_user_word_df(user_who_doesnt_exist)
        assert isinstance(df, pd.DataFrame)
        assert set(df.index) == set(prolix.read_words().index)
        assert {'right', 'wrong'}.issubset(set(df.columns))
        assert (df == 0).all().all()

    def test_user_answered_correct(self, correctly_answered_df, random_words):
        breakpoint()




class TestUserManagement:
    """ tests for creating and deleting users """
    def test_delete_non_existant_user(self):
        """ ensure deleting a user that doesn't exist fails silently """
        try:
            prolix.delete_user(user_who_doesnt_exist)
        except peewee.PeeweeException:
            pytest.fail('should not raise')

    def test_get_default_user_not_set(self):
        """ The default user should not be set. """
        assert prolix.user._get_default_user() is None

    def test_get_default_user_set(self, user):
        """ When user fixture is invoked the user should be set. """
        assert prolix.user._get_default_user() == user
