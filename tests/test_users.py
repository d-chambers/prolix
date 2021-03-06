"""
Tests for user features
"""

import numpy as np
import peewee
import pytest

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
        user.discard_word(random_words)
        return user

    def test_discarded_words_recorded(self, random_words, user_dwords):
        """ Ensure the discarded words are recorded and returned """
        words = user_dwords.get_discarded_words()
        assert set(words) == set(random_words)


class TestUserAnswerTable:
    """ Test getting a df of how the user has answered the words. """

    @pytest.fixture
    def correctly_answered_df(self, user, random_words):
        """ DF of a user who has correctly answered some words. """
        user.correctly_answered_word(random_words)
        return user.get_quiz_df()

    def test_user_answered_correct(self, correctly_answered_df, random_words):
        """ All the random words should have been answered correctly. """
        df = correctly_answered_df.loc[random_words]
        assert (df['right'] == 1).all()


class TestUserManagement:
    """ tests for creating and deleting users """

    def test_delete_non_existant_user(self):
        """ ensure deleting a user that doesn't exist fails silently """
        user = prolix.User(name=user_who_doesnt_exist)
        try:
            user.delete_user()
        except peewee.PeeweeException:
            pytest.fail('should not raise')

    def test_get_default_user_not_set(self):
        """ The default user should not be set. """
        assert prolix.User().name is None

    def test_get_default_user_set(self, user):
        """ When user fixture is invoked the user should be set. """
        assert prolix.User().name == user.name
