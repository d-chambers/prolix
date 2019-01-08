"""
Tests for administering the quiz
"""
from string import ascii_lowercase

import numpy as np
import pytest

import prolix


let2num = {let: num for num, let in enumerate(ascii_lowercase)}
num2let = {num: let for num, let in enumerate(ascii_lowercase)}


df = prolix.read_words()
vocab_list = df.index


@pytest.fixture(scope='class', params=df.index.values)
def word_series(request):
    """ return a series of a random word. """
    df = prolix.read_words()
    return df.loc[request.param]


@pytest.fixture
def word_quiz(word_series):
    """ return a word quiz for a random word. """
    return prolix.WordQuiz(word=word_series.name)


class TestWordQuiz:
    """ Tests for single word quiz """

    def test_answer(self, word_quiz, word_series):
        """ Ensure the correct answer is in the str rep. """
        # ensure correct index works
        correct_ind = word_quiz.definitions.index(word_series.definition)
        assert word_quiz.answer(correct_ind)
        assert word_quiz.answer(num2let[correct_ind])
        # ensure incorrect indices do not
        for ind in range(len(word_quiz.definitions)):
            if ind == correct_ind:
                continue
            assert not word_quiz.answer(ind)
            assert not word_quiz.answer(num2let[ind])

    def test_str_rep(self, word_quiz):
        str_rep = str(word_quiz)
        assert isinstance(str_rep, str)
        assert word_quiz.word in str_rep
