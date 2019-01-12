"""
A module for storing words.
"""
import time
import warnings
from pathlib import Path

import pandas as pd

# a simple cache for the csv. Keys are "df" and "read_time". The latter is
# just the system time when the file was read. Useful to caching.
_word_cache = {}

# init pydictionaries main classs

# paths to default csv store and default dataframe columns
default_word_csv_path = Path(__file__).parent / 'data' / 'words.csv'
word_columns = ['definition']


def _read_economist_words(path: Path):
    path = Path(path)
    assert path.exists()
    out = []
    with path.open('r') as fi:
        text = fi.read()
    # split on blank lines, grab word and lowercase it.
    for line in text.split('\n\n'):
        word = line.split(':')[0].lower()
        assert word.isalpha()
        out.append(word)
    return out


def _read_textlist(path: Path):
    """
    Adds a simple text file of words to the list
    """
    path = Path(path)
    assert path.exists()
    out = []
    with path.open('r') as fi:
        for line in fi.readlines():
            out.append(line.rstrip().lower())
    return out


def add_words(words) -> pd.DataFrame:
    """ Read the words in the words.txt file, generate csv. """
    # ensure words are in a sequence, not a single str
    from autocorrect import spell

    words = words if isinstance(words, str) else words
    out = []
    existing_words = read_words()
    pydict = None
    for word in words:
        corrected_word = spell(word)
        if corrected_word in existing_words.index:
            continue
        # pydict is rather heavy, only import it when needed
        from PyDictionary import PyDictionary
        pydic = pydict or PyDictionary()

        if word != corrected_word:
            msg = f'{word} not valid, correcting to {corrected_word}'
            warnings.warn(msg)
        print(f'fetching definition for word: {word}')
        out.append(dict(
            word=corrected_word,
            definition=pydic.meaning(corrected_word),
        ))
    if out:  # if there are any new words to add
        df = pd.DataFrame(out).set_index('word').sort_index()
        _commit_word_db(df)


def read_words():
    """ return a dataframe of words. """
    # determine if cache is to be used
    if _word_cache:
        assert {'df', 'read_time'}.issubset(_word_cache)
        last_modified = default_word_csv_path.stat().st_mtime
        cache_time = _word_cache.get('read_time', 0)
        # if file has been updated since last cache clear cache and return
        if last_modified > cache_time:
            _word_cache.clear()
            return read_words()
        else:
            df = _word_cache['df']
            assert not df.definition.isnull().any(), 'missing definitions'
            return df
    try:
        df = pd.read_csv(default_word_csv_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=word_columns)
    else:
        # remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')].set_index('word')
        # remove words with no definitions
        df = df[~df.definition.isnull()]
    assert set(df.columns) == set(word_columns)
    # add df to cache
    _word_cache['df'] = df.sort_index()
    _word_cache['read_time'] = time.time()
    return read_words()


def _commit_word_db(df, append=True):
    """ Commit a dataframe back to word store. """
    if append:
        df_old = read_words()
        df = pd.concat([df_old, df])
    df = df[~df.index.duplicated(keep='first')]
    df.to_csv(default_word_csv_path)
