"""


Edit:
    2013-11-26    added direction, probability, hypothetical, etc. to Word and children
"""
import re
from functools import total_ordering

from regex import Pattern


@total_ordering
class Word(object):
    __slots__ = ['word', 'begin', 'end', 'kind', 'offset',
                 'certainty', 'hypothetical', 'other', 'historical',
                 'direction', 'qualifiers']

    def __init__(self, word, begin, end, kind='term', offset=0):
        if isinstance(word, Pattern):
            self.word = word.pattern
        else:
            self.word = str(word)
        self.begin = begin
        self.end = end
        self.kind = kind.lower()
        self.offset = offset
        self.certainty = 4  # 0-4 (neg to affm)
        self.hypothetical = False  # for status only
        self.other = False  # for status only
        self.historical = False  # for status only
        self.direction = 0
        self.qualifiers = []

    @property
    def absolute_begin(self):
        return self.begin + self.offset

    @property
    def absolute_end(self):
        return self.end + self.offset

    @property
    def negated(self):
        return self.certainty == 0

    @property
    def improbable(self):
        return self.certainty == 1

    @property
    def possible(self):
        return self.certainty == 2

    @property
    def probable(self):
        return self.certainty == 3

    @property
    def affirmed(self):
        return self.certainty == 4

    def negate(self, qualifier=None):
        self.certainty = 0
        if qualifier:
            self.qualifiers.append(qualifier)

    def set_improbable(self, qualifier=None):
        if self.certainty > 1:  # added 20140109
            self.certainty = 1
            if qualifier:
                self.qualifiers.append(qualifier)

    def set_possible(self, qualifier=None):
        if self.certainty > 2:  # added 20140109
            self.certainty = 2
            if qualifier:
                self.qualifiers.append(qualifier)

    def set_probable(self, qualifier=None):
        if self.certainty > 3:  # added 20140109
            self.certainty = 3
            if qualifier:
                self.qualifiers.append(qualifier)

    def set_hypothetical(self, qualifier=None):
        self.hypothetical = True
        if qualifier:
            self.qualifiers.append(qualifier)

    def set_historical(self, qualifier=None):
        self.historical = True
        if qualifier:
            self.qualifiers.append(qualifier)

    def set_other_subject(self, qualifier=None):
        self.other = True
        if qualifier:
            self.qualifiers.append(qualifier)

    def __len__(self):
        return self.end - self.begin

    ''' Comparisons defined by relative location
        in the sentence. First term < last term. '''

    def __gt__(self, other):
        return self.begin > other.begin and self.end > other.end  # must account for eq implementation

    def __eq__(self, other):
        """ equal if any overlap in indices """
        return (self.begin == other.begin or
                self.end == other.end or
                (self.begin > other.begin and self.end < other.end) or
                (self.begin < other.begin and self.end > other.end)
                )

    def __unicode__(self):
        return str(self.word)

    def __str__(self):
        return str(self).encode('utf-8')

    def __repr__(self):
        return ('<' + str(self.word) + ',' + str(self.begin) + ':' +
                str(self.end) +
                (',NEG' if self.negated else ',POS' if self.possible else '') +
                ', <' + self.kind + '>>')


class Term(Word):
    __slots__ = ['id']

    def __init__(self, word, begin, end, kind, id_, offset=0):
        super(Term, self).__init__(word, begin, end, kind, offset)
        self.id = id_

    def id_as_list(self):
        return self.id if isinstance(self.id, list) else [self.id]

    def add_term(self, other):
        self.id = self.id_as_list() + other.id_as_list()


class Concept(Term):
    __slots__ = ['cat']

    def __init__(self, word, begin, end, id_, cat, certainty=4,
                 hypothetical=0, historical=0, not_patient=0, offset=0,
                 qualifiers=None):
        """
        For backwards compatibility:
            certainty used to be neg(ated), boolean
            hypothetical used to be pos(sible), boolean
        """
        super(Concept, self).__init__(word, begin, end, 'concept', id_, offset=offset)
        self.cat = cat
        self.certainty = certainty
        self.hypothetical = hypothetical
        self.historical = historical
        self.other = not_patient
        self.qualifiers = qualifiers or []


class Negation(Word):
    __slots__ = ['direction']

    def __init__(self, word, begin, end, kind='negn', direction=0, offset=0):
        super(Negation, self).__init__(word, begin, end, kind, offset=offset)
        self.direction = direction
        self.negate()


def find_terms(terms, text, offset=0):
    """
    Parameters:
        terms - list of (term,id) where unique id for each term
        :param terms:
        :param text:
        :param offset:
    """
    results = []
    for term, id_ in terms:
        for m in term.finditer(text):
            results.append(Term(term, m.start(), m.end(), 'term', id_, offset=offset))
    return sorted(results)


def clean_terms(terms):
    """
    remove terms that are subsumed by other terms
    :param terms:
    """
    terms.sort(reverse=False)
    if len(terms) < 2:
        return terms
    i = 1
    curr = 0
    while True:
        if terms[curr] == terms[i]:
            if len(terms[curr]) > len(terms[i]):
                del terms[i]
            elif len(terms[curr]) < len(terms[i]):
                del terms[curr]
                curr = i - 1
            elif terms[curr].begin == terms[i].begin and terms[curr].begin == terms[i].begin:
                terms[curr].add_term(terms[i])
                del terms[i]
            else:  # keep both representations
                curr = i
                i += 1
        else:
            curr = i
            i += 1

        if i >= len(terms):
            return terms


def add_words(terms, text, offset=0):
    """
    Adds fill words between concepts (i.e., terms) from the text
    based on begin and end offsets.
    NB: Ignores extraneous words before and after concepts
    since these do not play any role in combining terms
    or determining negation.
    :param terms:
    :param text:
    :param offset:
    """
    curr = 0
    words = []
    for term in sorted(terms):
        if term.begin > curr:
            for word in text[curr:term.begin].split():
                words.append(Word(word, curr + 1, curr + 1 + len(word), offset=offset))
                curr = curr + 1 + len(word)
        curr = term.end
    return words
