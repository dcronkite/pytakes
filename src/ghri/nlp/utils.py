"""
Author: David Cronkite, GHRI
Date: 4apr13
Description:
    Utility functions for repeated NLP use.
"""

import re


def ssplit(texts):
    """ 
    Basic sentence splitting module which will also replace
    stray '~~' and '~' assumed as input for some pathology
    data.
    """
    ssplitP = re.compile(r'(\S.+?[.!?\n])(?=\s+|$)')
    sections = []
    for text in texts:
        if not text: continue
        text = text.strip() + '\n'
        if text == '' or text == '\n': continue
        line = text.replace('\n', '\n ').replace('~~', '\n ')
        line = line.replace('~', ' ').replace('     ', ' ')
        line = line.replace('  ', ' ').replace('  ', ' ')
        result = re.findall(ssplitP, line)
        if result:
            sections += [res.strip() for res in result]
        else:
            sections += [line.strip()]
    return sections


def psplit(texts):
    """
    Phrase splitting.
    """
    if isinstance(texts, basestring):
        texts = [texts]
    ssplitP = re.compile(r'(\S.+?[.!?\n;:])(?=\s+|$)')
    sections = []
    for text in texts:
        if not text: continue
        text = text.strip() + '\n'
        if text == '' or text == '\n': continue
        line = text.replace('\n', '\n ').replace('~~', '\n ')
        line = line.replace('~', ' ').replace('     ', ' ')
        line = line.replace('  ', ' ').replace('  ', ' ')
        result = re.findall(ssplitP, line)
        if result:
            sections += [res.strip() for res in result]
        else:
            sections += [line.strip()]
    return sections


def replace_punctuation(text):
    import string

    return text.translate(string.maketrans('', ''), string.punctuation)


def is_number(s):
    try:
        float(s)
    except ValueError:
        return False
    return True

