"""
User Module and database stuff.
"""
from contextlib import suppress
from functools import wraps
from pathlib import Path
from typing import Optional, Set

import pandas as pd
import peewee

import prolix
from prolix import database_path
from prolix.utils import iterate

database = peewee.SqliteDatabase(database_path)

# a cache of tables {user: (rejected_table, quiz_table)}
_USER_CACHE = {}


class Meta:
    """ Base metaclass for dynamically created tables. """
    database = database


# --- database operations


def _create_table(table: peewee.Model):
    """ Try to create table, if it already exists pass. """
    with suppress(peewee.OperationalError):
        table.create_table()
    return table


def _delete_table(table: peewee.Model):
    """ Try to delete a table, if it doesn't exist pass. """
    with suppress(peewee.OperationalError):
        table.delete()
    return table


# --- Tables and table factories


class ProlixUsers(peewee.Model):
    """ A table for storing the names of prolix users. """
    user = peewee.CharField()
    Meta = Meta


# create the meta/user table
_create_table(ProlixUsers)


def _get_rejected_table(user) -> peewee.Model:
    """ Create a rejected words table for user. """
    contents = {'word': peewee.CharField(), 'Meta': Meta}
    cls = type(f'discarded_{user}', (peewee.Model,), contents)
    return cls


def _get_quiz_table(user) -> peewee.Model:
    """ Create a table for how often user gets certain words correct. """
    contents = {
        'word': peewee.CharField(),
        'right': peewee.IntegerField(default=0),
        'wrong': peewee.IntegerField(default=0),
        'Meta': Meta,
    }
    cls = type(f'quiz_{user}', (peewee.Model,), contents)

    return cls


def _add_user_to_db(user: str, set_current: bool = True):
    """
    Add a user to the database.

    Parameters
    ----------
    user
        A string identifying the user.
    set_current
        If True set the user to default user.
    """
    if user is None:
        return
    if user not in _USER_CACHE:
        reject_table = _create_table(_get_rejected_table(user))
        quiz_table = _create_table(_get_quiz_table(user))
        _USER_CACHE[user] = (reject_table, quiz_table)
    if set_current:
        _set_current_user(user)
    return user


def _get_current_user_name() -> Optional[str]:
    """ Get the current user, return None if one is not set. """
    path = Path(prolix.user_file_path)
    try:
        with path.open('r') as fi:
            return fi.read().rstrip() or None
    except FileNotFoundError:
        return None


def _set_current_user(user: Optional[str] = None):
    """
    Set the current user. If None delete current user.

    Parameters
    ----------
    user
        The name of the user
    """
    path = Path(prolix.user_file_path)
    # if user is None delete
    if user is None:
        with suppress(FileNotFoundError):
            path.unlink()
    else:
        with path.open('w') as fi:
            fi.write(user)


def _increment_word_count(words, field, user=None):
    """ increment the word count for correct or incorrect. """
    assert field in {'right', 'wrong'}
    # get the user and tables
    user = _add_user_to_db(user or _get_current_user_name())
    if user is None:
        return
    table = _USER_CACHE[user][1]
    # try to get the row for the word. Create if it doesn't exist
    for word in iterate(words):
        try:
            row = table.get(word=word)
        except peewee.DoesNotExist:
            data = {'word': word, field: 1}
            table.create(**data)
        else:
            current_value = getattr(row, field, 0)
            setattr(row, field, current_value + 1)


def _require_user(method):
    """
    Method decorator to require a user. If user is None don't call method.
    Also ensure the user has been created.
    """

    @wraps(method)
    def _wrap(self, *args, **kwargs):
        if self.name is not None:
            _add_user_to_db(self.name, self.is_current_user)
            return method(self, *args, **kwargs)

    return _wrap


class User:
    """ A prolix user model. """

    def __init__(self, name: Optional[str] = None,
                 is_current_user: bool = False):
        self.name = name or _get_current_user_name()
        self.is_current_user = is_current_user
        # initialzed
        _add_user_to_db(name)

    @property
    def is_current_user(self):
        return _get_current_user_name() == self.name

    @is_current_user.setter
    def is_current_user(self, is_current: bool):
        current_user = _get_current_user_name()
        if is_current and self.name:
            _set_current_user(self.name)
        if not is_current:
            # If the current user is user set it back to None
            if current_user == self.name:
                _set_current_user(None)

    @_require_user
    def delete_user(self):
        """ Delete this user, remove from db and delete current user if one
         exists. """
        # pull name out of cache and delete tables
        tables = _USER_CACHE.pop(self.name, [])
        for table in tables:
            _delete_table(table)
        # delete user from table
        with suppress(peewee.OperationalError, peewee.DoesNotExist):
            ProlixUsers.get(user=self.name).delete_instance()
        # reset current_user file
        if self.name == _get_current_user_name():
            _set_current_user(None)

    @staticmethod
    def _default_quiz_table() -> pd.DataFrame:
        """ Return the default quiz table. """
        df = prolix.read_words().copy()
        df['right'] = 0
        df['wrong'] = 0
        df = df[['right', 'wrong']]
        return df

    @_require_user
    def get_quiz_df(self) -> pd.DataFrame:
        """
        Return a datafame of word score for the user.

        The dataframe has the word as the index and "right" and "wrong" columns
        which are both integer counts of how many times the word quiz was answered
        correctly or incorrectly, respectively.

        """
        default = self._default_quiz_table()
        table = _USER_CACHE[self.name][1]
        df = pd.DataFrame(list(table.select().dicts()),
                          columns=['right', 'wrong', 'word'])
        return default.add(df.set_index('word'), fill_value=0)

    @_require_user
    def incorrectly_answered_word(self, word):
        """ User answered word incorrectly. """
        _increment_word_count(word, 'wrong', user=self.name)

    @_require_user
    def correctly_answered_word(self, word):
        """ User answered word correctly. """
        _increment_word_count(word, 'right', user=self.name)

    @_require_user
    def get_discarded_words(self) -> Set[str]:
        """ Return a set of discarded flashcard words for user. """
        table = _USER_CACHE[self.name][0]
        words = {x.word for x in table.select(table.word)}
        return words

    @_require_user
    def discard_word(self, word):
        """ Discard a word so that the flash card is not shown again. """
        table = _USER_CACHE[self.name][0]
        data = [{'word': x} for x in iterate(word)]
        table.insert_many(data).execute()
