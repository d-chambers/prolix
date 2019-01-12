"""
Utilities
"""

import ast
from functools import reduce
from typing import Optional
from operator import add


def _dedict_definition(word_def: str):
    """ de-dictify the word definitions """
    word_def = ast.literal_eval(word_def)
    return reduce(add, list(word_def.values()))


def _format_defintion(definition, number: Optional[int]=None):
    """ Format a definition for nice viewing. """
    fdefs = _dedict_definition(definition)
    joined = ':\n'.join(fdefs)
    if number:
        joined = f'{number}. ' + joined
    return joined


class FakeLoop:
    """ Fake urwid loop for debugging without screwing up stdout. """
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        pass

    def draw_screen(self, *args, **kwargs):
        pass