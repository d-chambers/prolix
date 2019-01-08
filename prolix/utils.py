"""
Utilities
"""

import ast
from functools import reduce
from operator import add


def _dedict_definitions(word_def: str):
    """ de-dictify the word definitions """
    if isinstance(word_def, str):
        word_def = ast.literal_eval(word_def)
    else:
        breakpoint()
    return reduce(add, list(word_def.values()))


class FakeLoop:
    """ Fake urwid loop for debugging without screwing up stdout. """
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        pass