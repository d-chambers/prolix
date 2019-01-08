"""
Core structures for the word quiz.
"""
import random
from functools import lru_cache
from string import ascii_lowercase
from textwrap import fill, indent
from typing import List, Union
from typing import Optional

import numpy as np
import urwid

import prolix
from prolix.utils import _dedict_definitions, FakeLoop

_letter_num_map = {let: num for num, let in enumerate(ascii_lowercase)}
_number_strings = {str(x) for x in range(10)}


def get_random_word(user=None) -> str:
    """
    Get a random word. If a user is specified favor words they have gotten
    wrong in the past.
    """
    df = prolix.read_words()
    return df.iloc[np.random.randint(0, len(df))].name


def _get_definitions(word: str, definition_count=4) -> List[str]:
    """
    Return a list of definitions with the correct definition as a member.

    Parameters
    ----------
    word
        The word for which a definition should be returned.
    definition_count
        The total number of definitions to return. If > 1 random definitions
        from other words will be mixed in.
    """
    df = prolix.read_words()
    inds = np.random.randint(0, len(df), definition_count)
    # make sure the correct index is not mixed in
    true_ind = np.argmax(df.index == word)
    # make sure True ind is no in inds
    inds_no_correct = list(set(inds) - {true_ind})
    # add correct ind and shuffle
    inds = ([true_ind] + inds_no_correct)[: definition_count]
    random.shuffle(inds)

    assert len(inds) == len(set(inds)), 'all index values must be unique'
    assert true_ind in inds, 'true index must be in index list'

    return list(df.definition.values[inds])


class WordQuiz:
    """ A class to quiz the user on a random, or selected word. """

    terminal_width = 70  # assumed spaces
    def_indent_width = 4

    def __init__(self, word: Optional[str] = None, definition_count: int = 4):
        self.word: str = word or get_random_word()
        self.definitions = _get_definitions(self.word, definition_count)

    @property
    def word_df(self):
        """ Return the current word dataframe. """
        return prolix.read_words()

    @property
    @lru_cache()
    def word_def_block(self):
        """ Return a list of formatted definitions """
        # definition block, displays
        word_defs = []
        for wdef in self.definitions:
            wdef_list = _dedict_definitions(wdef)
            # new_width = self.terminal_width - self.def_indent_width
            # split_subdefs = [fill(x, new_width) for x in wdef_list]
            word_defs.append(';\n'.join(wdef_list))
        # add answer numbers
        for num in range(len(word_defs)):
            word_defs[num] = f'{num + 1}.' + word_defs[num]
        return word_defs

    @property
    def _correct_index(self):
        """
        Return the index of the correct definition.
        """
        wdef = self.word_df.loc[self.word].definition
        return self.definitions.index(wdef)

    def answer(self, number: Union[str, int]) -> bool:
        """
        Try to select the correct definition from those in the definitions list.

        Parameters
        ----------
        number
            Either an int (eg 0, 1, 2) or a single character (a, b, c, d) which
            will be mapped to an element in the definitions list.

        Returns
        -------
        True if correct, else false.
        """
        ind = _letter_num_map.get(number, number)
        return ind == self._correct_index

    __call__ = answer

    def _fill_indent(self, txt):
        """ fill and indent text """
        return indent(fill(txt, self.terminal_width), self.def_indent_width)

    def gen_string(self) -> str:
        """
        Return a flash card style output.
        """
        # create title block which displays the word
        title = self.word.center(self.terminal_width)
        dashes = '-' * self.terminal_width
        title_block = '\n'.join([dashes, title, dashes]) + '\n'

        # get definition block
        word_defs = list(self.word_def_block)
        def_block = '\n\n'.join(word_defs)
        return '\n' + '\n'.join([title_block, def_block]) + '\n'

    __str__ = gen_string


class QuizRun:
    """ A class to control the entire quiz run. """

    # palette defining all styles used in display
    palette = [
        ('title', 'bold', ''),
        ('reversed', 'standout', ''),
        ('correct_def', 'bold', 'dark blue'),
    ]

    def __init__(self, question_count=15, user=None, definition_count=4):
        self._remaining_questions = question_count
        self.user = user
        self._buttons = []
        self._main = None
        self._def_count = definition_count
        self._get_new_word()
        self._get_question_list_box()
        self._debug = False  # set to True to avoid running loop
        self._loop = None
        # map indices of buttons in the simple list walker
        self._button_index = tuple(range(3, definition_count * 2 + 2, 2))

    def _get_new_word(self):
        self.word = WordQuiz(definition_count=self._def_count)
        self._remaining_questions -= 1
        self._answered_correctly = True

    def _get_question_list_box(self):
        """ Create a menu to display quiz questions. """
        # load title and choices, init header
        title = self.word.word
        choices = self.word.word_def_block
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

            if not self._answered_correctly and ind == self.word._correct_index:
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
        self.overlay = overlay

    def item_chosen(self, button, choice):
        is_correct = self.word.answer(choice)
        if is_correct:
            self._get_new_word()
        else:
            self._answered_correctly = False
        if self._remaining_questions < 1:
            urwid.ExitMainLoop()
        self._get_question_list_box()

    def exit_program(self, button=None):
        raise urwid.ExitMainLoop()

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

    def __call__(self):
        """ start the urwid loop. """
        Loop = urwid.MainLoop if not self._debug else FakeLoop
        kwargs = dict(palette=self.palette, unhandled_input=self._handle_input)
        self._loop = Loop(self.overlay, **kwargs).run()
