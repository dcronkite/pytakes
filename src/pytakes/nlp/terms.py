"""


Edit:
    2013-11-26    added direction, probability, hypothetical, etc. to Word and children
"""

from functools import total_ordering


@total_ordering
class Word(object):
    def __init__(self, word, begin, end, _type='term', offset=0):
        self.word_ = word
        self.begin_ = begin
        self.end_ = end
        self.type_ = _type.lower()
        self.offset_ = offset
        self.certainty_ = 4  # 0-4 (neg to affm)
        self.hypothetical_ = False  # for status only
        self.other_ = False  # for status only
        self.historical_ = False  # for status only
        self.direction_ = 0

    def get_absolute_begin(self):
        return self.begin() + self.offset_

    def get_absolute_end(self):
        return self.end() + self.offset_

    def is_negated(self, normal=True):
        if normal:
            return self.certainty_ == 0
        else:
            return not self.negated_

    def is_improbable(self):
        return self.certainty_ == 1

    def is_possible(self):
        return self.certainty_ == 2

    def is_probable(self):
        return self.certainty_ == 3

    def is_affirmed(self):
        return self.certainty_ == 4

    def get_certainty(self):
        return self.certainty_

    def set_certainty(self, level):
        self.certainty_ = level

    def is_hypothetical(self):
        return self.hypothetical_

    def is_historical(self):
        return self.historical_

    def is_not_patient(self):
        return self.other_

    def negate(self):
        self.certainty_ = 0

    def improbable(self):
        if self.certainty_ > 1:  # added 20140109
            self.certainty_ = 1

    def possible(self):
        if self.certainty_ > 2:  # added 20140109
            self.certainty_ = 2

    def probable(self):
        if self.certainty_ > 3:  # added 20140109
            self.certainty_ = 3

    def hypothetical(self):
        self.hypothetical_ = True

    def historical(self):
        self.historical_ = True

    def other_subject(self):
        self.other_ = True

    def direction(self):
        return self.direction_

    def begin(self):
        return self.begin_

    def set_begin(self, begin):
        self.begin_ = begin

    def end(self):
        return self.end_

    def set_end(self, end):
        self.end_ = end

    def word(self):
        return str(self.word_)

    def type(self):
        return self.type_

    def __len__(self):
        return self.end_ - self.begin_

    ''' Comparisons defined by relative location
        in the sentence. First term < last term. '''

    def __gt__(self, other):
        return self.begin_ > other.begin_ and self.end_ > other.end_  # must account for eq implementation

    def __eq__(self, other):
        """ equal if any overlap in indices """
        return (self.begin_ == other.begin_ or
                self.end_ == other.end_ or
                (self.begin_ > other.begin_ and self.end_ < other.end_) or
                (self.begin_ < other.begin_ and self.end_ > other.end_)
                )

    def __unicode__(self):
        return str(self.word_)

    def __str__(self):
        return str(self).encode('utf-8')

    def __repr__(self):
        return ('<' + str(self.word_) + ',' + str(self.begin_) + ':' +
                str(self.end_) +
                (',NEG' if self.is_negated() else ',POS' if self.is_possible else '') +
                ', <' + self.type_ + '>>')


class Term(Word):
    def __init__(self, word, begin, end, _type, id_, offset=0):
        super(Term, self).__init__(word, begin, end, _type, offset)
        self.id_ = id_

    def id(self):
        return self.id_

    def id_as_list(self):
        if isinstance(self.id_, list):
            return self.id_
        else:
            return [self.id_]

    def add_term(self, other):
        self.id_ = self.id_as_list() + other.id_as_list()


class Concept(Term):
    def __init__(self, word, begin, end, id_, cat, certainty=4,
                 hypothetical=0, historical=0, not_patient=0, offset=0):
        """
        For backwards compatibility:
            certainty used to be neg(ated), boolean
            hypothetical used to be pos(sible), boolean
        """
        super(Concept, self).__init__(word, begin, end, "concept", id_, offset=offset)
        self.cat_ = cat

        if isinstance(certainty, bool):  # old way
            neg = certainty
            pos = hypothetical
            if neg:
                self.negate()
            if pos:
                self.possible()

        else:  # new way
            self.set_certainty(certainty)
            if hypothetical:
                self.hypothetical()
            if historical:
                self.historical()
            if not_patient:
                self.other_subject()

    def cat(self):
        return self.cat_


class Negation(Word):
    def __init__(self, word, begin, end, _type='negn', direction=0, offset=0):
        super(Negation, self).__init__(word, begin, end, _type, offset=offset)
        self.direction_ = direction
        self.negate()


def find_terms(terms, text, offset=0):
    """
    Paramters:
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
            elif terms[curr].begin() == terms[i].begin() and terms[curr].end() == terms[i].end():
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
        if term.begin() > curr:
            for word in text[curr:term.begin()].split():
                words.append(Word(word, curr + 1, curr + 1 + len(word), offset=offset))
                curr = curr + 1 + len(word)
        curr = term.end()
    # ignoring extraneous words at end of sentence
    return words
