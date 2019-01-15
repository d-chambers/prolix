"""
Module for accessing user info.
"""
from contextlib import suppress
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


class MetaProlix(peewee.Model):
    """ A metatable that keeps track of version, current user, etc. """
    current_user = peewee.CharField()
    version = peewee.CharField()
    Meta = Meta


# create the meta table
_create_table(MetaProlix)


def _get_rejected_table(user) -> peewee.Model:
    """ Create a rejected words table for user. """
    contents = {'word': peewee.CharField(), 'Meta': Meta}
    cls = type(f'discarded_{user}', (peewee.Model,), contents)
    return cls


def _get_quiz_table(user) -> peewee.Model:
    """ Create a table for how often user gets certain words correct. """
    contents = {'word': peewee.CharField(), 'right': peewee.IntegerField(),
                'wrong': peewee.IntegerField(), 'Meta': Meta}
    cls = type(f'quiz_{user}', (peewee.Model,), contents)

    return cls


def create_user(user: str, set_default: bool = True):
    """
    Add a user to the database.

    Parameters
    ----------
    user
        A string identifying the user.
    set_default
        If True set the user to default user.
    """
    if user is None:
        return
    if user not in _USER_CACHE:
        reject_table = _create_table(_get_rejected_table(user))
        quiz_table = _create_table(_get_quiz_table(user))
        _USER_CACHE[user] = (reject_table, quiz_table)
    if set_default:
        result = (
            MetaProlix
                .insert(id=1, current_user=user, version=prolix.__version__)
                .on_conflict('replace').execute()
        )
        assert result
    return user


def delete_user(user):
    """ Delete a user from the database. """
    # pull name out of cache and delete tables
    tables = _USER_CACHE.pop(user, [])
    for table in tables:
        _delete_table(table)
    # delete set user if needed
    with suppress(peewee.OperationalError, peewee.DoesNotExist):
        MetaProlix.get(current_user=user).delete_instance()


def _get_default_user() -> Optional[str]:
    """ return the default user name or None if none is specified. """
    try:
        return MetaProlix.get_by_id(1).current_user
    except peewee.DoesNotExist:
        return


def get_discarded_words(user=None) -> Set[str]:
    """ Return a set of discarded flashcard words. """
    user = create_user(user or _get_default_user(), set_default=False)
    if user:
        table = _USER_CACHE[user][0]
        words = {x.word for x in table.select(table.word)}
        return words
    return set()


def discard_word(word, user=None):
    """ Discard a word so that the flash card is not shown again. """
    user = create_user(user or _get_default_user(), set_default=False)
    if user:
        table = _USER_CACHE[user][0]
        data = [{'word': x} for x in iterate(word)]
        table.insert_many(data).execute()


def _increment_word_count(words, field, user=None):
    """ increment the word count for correct or incorrect. """
    assert field in {'right', 'wrong'}
    # get the user and tables
    user = create_user(user or _get_default_user())
    if user is None:
        return
    table = _USER_CACHE[user][1]
    # try to get the row for the word. Create if it doesn't exist
    for word in iterate(words):
        try:
            row = table.get(word=word)
        except peewee.DoesNotExist:
            data = {'word': word, field: 1}
            row = table.create(**data).execute()
        else:
            current_value = getattr(row, field, 0)
            setattr(row, field, current_value + 1)


def _correctly_answered_word(word, user=None):
    """
    Increment the correct count for the word of user.

    Parameters
    ----------
    word
        The word that was answered.
    user
        The user who answered. If None use default user.
    """
    _increment_word_count(word, 'right', user=user)


def _incorrectly_answered_word(word, user=None):
    """
    Increment the incorrect count for the word of user.

    Parameters
    ----------
    word
        The word that was answered.
    user
        The user who answered. If None use default user.
    """
    _increment_word_count(word, 'wrong', user=user)


def _get_user_word_df(user=None):
    """
    Return a datafame of word score for the user.

    The dataframe has the word as the index and "right" and "wrong" columns
    which are both integer counts of how many times the word quiz was answered
    correctly or incorrectly, respectively.

    Parameters
    ----------
    user
        The user to query.
    """
    user = create_user(user or _get_default_user())
    table = _USER_CACHE[user][1]
    word_df = prolix.read_words()
    # get the existing databse
    df = pd.DataFrame(list(table.select().dicts()))
    if df.empty:
        df = word_df.copy()
        df['right'] = 0
        df['wrong'] = 0
        df = df[['right', 'wrong']]
    else:
        breakpoint()



    return df

