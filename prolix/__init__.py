"""
A flask/command line app for studying GRE vocab words.
"""
import prolix.store
import prolix.cli

# shortcut imports
from prolix.store import read_words, add_words
from prolix.core import WordQuiz, QuizRun, Card, CardRun
