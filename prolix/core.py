"""
Core structures for the word quiz.
"""
import abc
import random
from functools import lru_cache
from itertools import cycle
from string import ascii_lowercase
from typing import List, Union
from typing import Optional

import numpy as np
import urwid

import prolix
from prolix.utils import FakeLoop, _format_defintion

_letter_num_map = {let: num for num, let in enumerate(ascii_lowercase)}
_number_strings = {str(x) for x in range(10)}
_quiz_on = ('word', 'definition')


class ProlixUrWid:
    """ Base class for prolix classes that use urwid for GUI."""
    # palette defining all styles used in display
    palette = [
        ('title', 'bold', ''),
        ('reversed', 'standout', ''),
        ('correct_def', 'bold', 'dark blue'),
        ('header_block', 'yellow,bold', '')
    ]

    _debug = False
    _main = None
    _loop = None  #
    _has_exited = False  # if the quiz has exited
    _overlay = None
    _name = None
    _user = None
    _has_exited = False

    def __call__(self):
        """ start the urwid loop. """
        assert self._overlay is not None
        Loop = urwid.MainLoop if not self._debug else FakeLoop
        kwargs = dict(palette=self.palette, unhandled_input=self._handle_input)
        self._loop = Loop(self._overlay, **kwargs)
        self._loop.run()

    def exit_program(self, button=None):
        """ Exit the GUI. """
        self._has_exited = True
        if not self._debug:
            raise urwid.ExitMainLoop()

    @property
    def _header(self):
        """ Return header text block """
        name_block = f"{self._name or ''}"
        user_block = self._user.name or ""
        text = urwid.Text(name_block + user_block, align='center')
        return urwid.AttrMap(text, 'header_block')

    # --- abstract methods to be defined by subclass

    @abc.abstractmethod
    def _handle_input(self, key: str):
        """ A function to handle the input passed from user. """
        pass

    def _get_footer(self):
        """ Return the urwid components to put in the bottom of the frame. """
        # Note this will return a black string if not overwritten
        txt = ''
        return urwid.Text(txt)


def get_random_word(user=None) -> str:
    """
    Get a random word. If a user is specified favor words they have gotten
    wrong in the past.
    """
    df = prolix.read_words()
    return df.iloc[np.random.randint(0, len(df))].name


def _get_definitions(word: str, count=4) -> List[str]:
    """
    Return a list of definitions with the correct definition as a member.

    Parameters
    ----------
    word
        The word for which a definition should be returned.
    count
        The total number of definitions to return. If > 1 random definitions
        from other words will be mixed in.
    """
    df = prolix.read_words()
    inds = np.random.randint(0, len(df), count)
    # make sure the correct index is not mixed in
    true_ind = np.argmax(df.index == word)
    # make sure True ind is no in inds
    inds_no_correct = list(set(inds) - {true_ind})
    # add correct ind and shuffle
    inds = ([true_ind] + inds_no_correct)[: count]
    random.shuffle(inds)

    assert len(inds) == len(set(inds)), 'all index values must be unique'
    assert true_ind in inds, 'true index must be in index list'

    return list(df.definition.values[inds])


def _get_words(word: str, count=4) -> List[str]:
    """
    Return a list of words with the correct word included.

    Parameters
    ----------
    word
        The correct word to include.
    count
        The number of words to include in the list.
    """
    all_words = prolix.read_words().index
    choice = list(np.random.choice(all_words, count))
    unique = ([word] + list(set(choice) - {word}))[:count]
    random.shuffle(unique)
    return unique


# ----------------- Word Quiz stuff

class WordQuiz:
    """ A class to quiz the user on a random, or selected word. """

    def __init__(self, word: Optional[str] = None, count: int = 4):
        # load the word list
        df = prolix.read_words()
        # get the True word and definition
        self.word: str = word or get_random_word()
        self.definition = df.loc[self.word].values[0]
        # mix in correct words/definition with randomly selected ones for quiz
        self.quiz_words = _get_words(self.word, count)
        self.quiz_definitions = _get_definitions(self.word, count)

    @property
    def word_df(self):
        """ Return the current word dataframe. """
        return prolix.read_words()

    @property
    @lru_cache()
    def formatted_definition_list(self):
        """ Return a list of formatted definitions """
        # definition block, displays
        out = [_format_defintion(x, n + 1)
               for n, x in enumerate(self.quiz_definitions)]
        return out

    @property
    @lru_cache()
    def formatted_defintion(self):
        """ format only the correct definition. """
        return _format_defintion(self.definition)

    @property
    def _correct_def_index(self):
        """
        Return the index of the correct definition.
        """
        wdef = self.word_df.loc[self.word].definition
        return self.quiz_definitions.index(wdef)

    @property
    def _correct_word_index(self):
        """
        Return the index of the correct word.
        """
        return self.quiz_words.index(self.word)

    def answer_def(self, number: Union[str, int]) -> bool:
        """
        Try to select the correct definition from those in the definitions list.

        Parameters
        ----------
        number
            Either an int (eg 0, 1, 2) or a single character (a, b, c, d) which
            will be mapped to an element in the definitions list.

        Returns
        -------
        True if correct, else False.
        """
        ind = _letter_num_map.get(number, number)
        return ind == self._correct_def_index

    def answer_word(self, number: Union[str, int]) -> bool:
        """
        Try to select the correct word from those in the definitions list.

        Parameters
        ----------
        number
            Either an int (eg 0, 1, 2) or a single character (a, b, c, d) which
            will be mapped to an element in the definitions list.

        Returns
        -------
        True if correct, else False.
        """
        ind = _letter_num_map.get(number, number)
        return ind == self._correct_word_index

    def answer(self, number, quiz_on='word'):
        """ Answer the question based on quiz_on mode. """
        if quiz_on == 'word':
            return self.answer_def(number)
        elif quiz_on == 'definition':
            return self.answer_word(number)

    def _get_correct_ind(self, quiz_on='word'):
        """ Return the correct index based on if words or defs are being tested """
        if quiz_on == 'word':
            return self._correct_def_index
        elif quiz_on == 'definition':
            return self._correct_word_index

    def __str__(self) -> str:
        """
        Return a flash card style output.
        """
        correct_def = self.formatted_definition_list[self._correct_def_index]
        correct_line = f'{self.word}: {correct_def}'
        qwords = f'quiz words: {self.quiz_words}'
        qdefs = f'quiz definitions: {self.formatted_definition_list}'
        return '\n'.join([correct_line, qwords, qdefs]) + '\n'


class QuizRun(ProlixUrWid):
    """
    A class to control the entire quiz run.

    Parameters
    ----------
    question_count
       The number of questions to ask before exiting.
    user
       The name of the user if stats are to be kept. If not specified use
       the last set user. If None don't keep stats.
    choice_count
        The number of choices to give the user
    quiz_on
        Indicates to quiz the user on words or definitions. If "word" then show
        once word and have the user select the definition. If "definition" then
        show the user a single definition and have the user select the word.
    """

    # set defaults
    _answered_correctly = True
    _name = 'Prolix Word Quiz'

    def __init__(self, question_count=15, user=None, choice_count=4, quiz_on='word'):
        self._remaining_questions = question_count
        self._user = prolix.User(user)
        self._buttons = []
        assert quiz_on in {'word', 'definition'}
        self._quiz_on = quiz_on
        self._def_count = choice_count
        self._get_new_quiz()
        self._create_display()
        self._quiz_on_cycle = cycle(_quiz_on)

        # map indices of buttons in the simple list walker
        self._button_index = tuple(range(3, choice_count * 2 + 2, 2))

    def _get_new_quiz(self):
        self.quiz = WordQuiz(count=self._def_count)
        self._remaining_questions -= 1
        self._answered_correctly = True

    def _get_title_and_choices(self):
        """ return a list of title to display and choices based on quiz type. """
        if self._quiz_on == 'word':
            title = self.quiz.word
            choices = self.quiz.formatted_definition_list
        else:
            assert self._quiz_on == 'definition'
            title = self.quiz.formatted_defintion
            choices = self.quiz.quiz_words
        return title, choices

    def _create_display(self):
        """ Create a menu to display quiz questions. """
        # load title and choices, init header
        title, choices = self._get_title_and_choices()
        correct_ind = self.quiz._get_correct_ind(self._quiz_on)
        # init
        self._buttons = []
        self.title_text = urwid.Text(title, align='center')
        self.body_text = [urwid.Divider(), urwid.AttrMap(self.title_text, 'title')]
        for ind, c in enumerate(choices):
            # add divider to keep things nicely spaced
            self.body_text.append(urwid.Divider())
            # create buttons (each on is a definition that can be selected)
            button = urwid.Button(c)
            self._buttons.append(button)
            urwid.connect_signal(button, 'click', self.item_chosen, ind)

            if not self._answered_correctly and ind == correct_ind:
                button_map = urwid.AttrMap(button, 'correct_def')
            else:
                button_map = urwid.AttrMap(button, None)
            self.body_text.append(button_map)

        self._list_walker = urwid.SimpleFocusListWalker(self.body_text)
        list_box = urwid.ListBox(self._list_walker)
        # put the listbox into an overlay and return
        if self._main is None:
            self._main = urwid.Padding(list_box, left=2, right=2)
        else:
            self._main.original_widget = list_box

        overlay = urwid.Overlay(self._main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                                align='center', width=('relative', 90),
                                valign='middle', height=('relative', 60),
                                min_width=40, min_height=20)

        frame = urwid.Frame(header=self._header, body=overlay,
                            footer=self._get_footer())

        self._overlay = frame

    def item_chosen(self, button, choice):
        """
        The user has chosen an item, determine if it is correct.

        If so, got to next question else highlight correct answer.
        """
        is_correct = self.quiz.answer(choice, quiz_on=self._quiz_on)

        if is_correct:
            if self._answered_correctly:
                self._user.correctly_answered_word(self.quiz.word)
            self._get_new_quiz()
        else:
            self._answered_correctly = False
            self._user.incorrectly_answered_word(self.quiz.word)
        if self._remaining_questions < 1:
            self.exit_program()
        self._create_display()

    def _answer_correctly(self):
        """ Answer the current question correctly, used only for debugging. """
        if self._quiz_on == 'word':
            self.item_chosen(None, self.quiz._correct_def_index)
        elif self._quiz_on == 'definition':
            self.item_chosen(None, self.quiz._correct_word_index)

    def _handle_input(self, key):
        """ Handle input not taken care of by menu. """
        # q is for quit, that's good enough for me
        if key in {'q', 'Q'}:
            self.exit_program(key)
        # the user is already at the top, roll to the bottom
        elif key == 'down':
            self._list_walker.set_focus(self._button_index[0])
        elif key == 'up':
            self._list_walker.set_focus(self._button_index[-1])
        elif key in _number_strings:
            val = int(key) - 1
            if val > self._def_count - 1:
                return
            focus_val = self._button_index[val]
            # if this item is getting double selected, simulate click
            if focus_val == self._list_walker.focus:
                self._buttons[val]._emit('click')
            else:  # else just select it
                self._list_walker.set_focus(focus_val)
        elif key == 'f':  # flip mode for next card
            current = self._quiz_on
            self._quiz_on = next(self._quiz_on_cycle)
            if self._quiz_on == current:
                self._quiz_on = next(self._quiz_on_cycle)

    def _get_footer(self):
        txt = 'q: quit; f: flip mode on next card; arrows or numbers select answer'
        return urwid.Text(txt)


# -------------------- Flash card stuff

class Card:
    """ A simple flash card. """

    def __init__(self, word: Optional[str] = None):
        # load the word list
        df = prolix.read_words()
        # get the True word and definition
        self.word: str = word or get_random_word()
        self.definition = df.loc[self.word].values[0]
        self.formated_definition = _format_defintion(self.definition)

        self.side = 'word'
        # iterators for flipping card
        self.fliperator = cycle([self.formated_definition, self.word])
        self.siderator = cycle(['definition', 'word'])
        # the text currently displayed
        self.displayed_text = self.word

    def flip(self):
        """ Flip the card over. """
        self.displayed_text = next(self.fliperator)
        self.side = next(self.siderator)


class CardRun(ProlixUrWid):
    """
    Controller class for a flash card run.

    Parameters
    ----------
    start_on
        Indicates if the flash cards should start on the word or definition.
    """
    card = None
    _name = 'Prolix Flash Cards'

    def __init__(self, start_on='word', user: Optional[str] = None):
        assert start_on in {'word', 'definition'}
        self._side = start_on
        self._user = user
        self.words = list(prolix.read_words().index.values)
        self.draw_card()
        self._create_display()

    def draw_card(self):
        """ randomly draw a card from the candidate_words pile. """
        if not self.words:  # no more cards to draw
            self.exit_program()
            return
        # else randomly select a card
        word = np.random.choice(self.words)
        self.card = Card(word)
        # if the card is to start on the definition we need to flip it
        if self._side == 'definition':
            self.card.flip()

    def _handle_input(self, key):
        """ Handle input not taken care of by menu. """
        mouse_clicked = isinstance(key, tuple) and key[0] == 'mouse press'
        # q is for quit, that's good enough for me
        if key in {'q', 'Q'}:
            self.exit_program(key)
        # the user swipes right to keep the card
        elif key == 'right':
            self.draw_card()
        # the user swipes left to no longer be able to draw the card
        elif key == 'left':
            self.words.remove(self.card.word)
            self.draw_card()
        # the user wants to flip the card over
        elif key == 'f' or mouse_clicked:
            self.card.flip()
            self._side = self.card.side
        self._create_display()

    def _create_display(self):
        """ Create a menu to display quiz questions. """
        # only need to updated text
        txt_input = ('title', self.card.displayed_text)
        if self._main is not None:
            if not self._loop:  # make sure loop has been inited
                self()
            self._main.base_widget.set_text(txt_input)
            self._loop.draw_screen()
            return
        text = urwid.Text(txt_input, align='center')
        # else generate frame
        fill = urwid.Filler(text)
        v_padding = urwid.Padding(fill, left=1, right=1)
        # update or create new main textbox widget
        self._main = urwid.LineBox(v_padding)

        # set layout and exit
        layout = urwid.Frame(header=self._header, body=self._main,
                             footer=self._get_footer())
        self._overlay = layout

    def _get_footer(self):
        txt = 'q: quit; f: flip card; \u2192 next card; \u2190 discard card'
        return urwid.Text(txt)
