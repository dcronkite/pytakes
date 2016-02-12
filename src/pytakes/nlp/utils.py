"""
Author: David Cronkite, GHRI
Date: 4apr13
Description:
    Utility functions for repeated NLP use.
"""

import regex as re
from datetime import datetime


def ssplit(texts):
    """ 
    Basic sentence splitting module which will also replace
    stray '~~' and '~' assumed as input for some pathology
    data.
    """
    ssplit_p = re.compile(r'(\S.+?[.!?\n])(?=\s+|$)')
    sections = []
    for text in texts:
        if not text: continue
        text = text.strip() + '\n'
        if text == '' or text == '\n': continue
        line = text.replace('\n', '\n ').replace('~~', '\n ')
        line = line.replace('~', ' ').replace('     ', ' ')
        line = line.replace('  ', ' ').replace('  ', ' ')
        result = re.findall(ssplit_p, line)
        if result:
            sections += [res.strip() for res in result]
        else:
            sections += [line.strip()]
    return sections


def psplit(texts):
    """
    Phrase splitting.
    """
    if isinstance(texts, str):
        texts = [texts]
    ssplit_p = re.compile(r'(\S.+?[.!?\n;:])(?=\s+|$)')
    sections = []
    for text in texts:
        if not text: continue
        text = text.strip() + '\n'
        if text == '' or text == '\n': continue
        line = text.replace('\n', '\n ').replace('~~', '\n ')
        line = line.replace('~', ' ').replace('     ', ' ')
        line = line.replace('  ', ' ').replace('  ', ' ')
        result = re.findall(ssplit_p, line)
        if result:
            sections += [res.strip() for res in result]
        else:
            sections += [line.strip()]
    return sections


def replace_punctuation(text):
    return re.sub(r"\p{P}+", "", text)


def is_number(s):
    try:
        float(s)
    except ValueError:
        return False
    return True


def convert_sql_datetime_to_python(datestring):
    return datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S.%f')
