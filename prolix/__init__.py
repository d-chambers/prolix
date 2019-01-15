"""
A flask/command line app for studying GRE vocab words.
"""
from pathlib import Path


from .version import __version__

# get datapath
data_path = Path(__file__).parent / 'data'
database_path = data_path / '.prolix.db'

import prolix.store
import prolix.cli

# shortcut imports
from prolix.store import read_words, add_words
from prolix.core import WordQuiz, QuizRun, Card, CardRun
from prolix.user import create_user, delete_user



