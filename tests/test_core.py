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


@pytest.fixture(scope='class')
def word_quiz(word_series):
    """ return a word quiz for a random word. """
    return prolix.WordQuiz(word=word_series.name)


@pytest.fixture
def word_quiz_run():
    """ return a QuizRun instance to quiz on words. """
    qr = prolix.QuizRun(quiz_on='word')
    qr._debug = True
    return qr


@pytest.fixture
def def_quiz_run():
    """ return a QuizRun instance on the definition. """
    qr = prolix.QuizRun(quiz_on='definition')
    qr._debug = True
    return qr


@pytest.fixture(params=['def_quiz_run', 'word_quiz_run'])
def quiz_run(request):
    """ collect the other quiz run fixtures. """
    return request.getfixturevalue(request.param)


@pytest.fixture
def card_run():
    """ A simple flash card usage. """
    cr = prolix.CardRun()
    cr._debug = True
    return cr


class TestWordQuiz:
    """ Tests for single word quiz """

    def test_answer_definitions(self, word_quiz, word_series):
        """ Ensure the correct answer is in the str rep. """
        # ensure correct index works
        correct_ind = word_quiz.quiz_definitions.index(word_series.definition)
        assert correct_ind == word_quiz._correct_def_index
        assert word_quiz.answer_def(correct_ind)
        assert word_quiz.answer(num2let[correct_ind], quiz_on='word')
        # ensure incorrect indices do not
        for ind in range(len(word_quiz.quiz_definitions)):
            if ind == correct_ind:
                continue
            assert not word_quiz.answer_def(ind)
            assert not word_quiz.answer_def(num2let[ind])
        assert word_quiz.answer_def(word_quiz._correct_def_index)

    def test_answer_words(self, word_quiz, word_series):
        """ Ensure the correct word answer works. """
        # ensure correct index works
        correct_ind = word_quiz.quiz_words.index(word_series.name)
        assert correct_ind == word_quiz._correct_word_index
        assert word_quiz.answer_word(correct_ind)
        assert word_quiz.answer(num2let[correct_ind], quiz_on='definition')
        # ensure incorrect indices do not
        for ind in range(len(word_quiz.quiz_words)):
            if ind == correct_ind:
                continue
            assert not word_quiz.answer_word(ind)
            assert not word_quiz.answer_word(num2let[ind])
        assert word_quiz.answer_word(word_quiz._correct_word_index)

    def test_str_rep(self, word_quiz):
        str_rep = str(word_quiz)
        assert isinstance(str_rep, str)
        assert word_quiz.word in str_rep


class TestQuizRun:
    """ tests for the quiz run """
    def test_program_ends(self, quiz_run):
        """ Answer all questions correctly and ensure quiz ends. """
        for num in range(quiz_run._remaining_questions + 1):
            quiz_run._answer_correctly()
        assert quiz_run._has_exited


class TestCard:
    def test_flip(self):
        """ make sure the text changes when the card is flipped. """
        card = prolix.Card()
        text = card.displayed_text
        card.flip()
        assert text != card.displayed_text
        card.flip()
        assert text == card.displayed_text


class TestCardRun:
    """ tests for running through the cards. """

    def test_cards_run_out(self, card_run):
        """ ensure cards run out after all are discarded. """
        word_len = len(prolix.read_words())
        for _ in range(word_len):
            card_run._handle_input('left')
        assert card_run._has_exited

