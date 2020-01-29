"""
downloaded from http://code.google.com/p/negex/downloads/detail?name=negex.python.zip
on 9 July 2012

General NegEx Python Implementation v.1.2 (Peter Kang) & De-Identified Annotations (Chapman)

Edits:
    2012-07-09  - added isNegated and isAffirmed boolean methods
                - added return statement to __str__ method
    2012-12-10  - added sortRules2
    2013-04-17  - added sortRulesFromTuple (for database integration)
                - added myNegTagger class (customization of negTagger)
    2013-11-25  - added myStatusTagger class (expands myNegTagger for use with historical, etc.)
    2013-12-09  - added getNegex and getContext functions; I'm going to need these each
                time I use negex, so might as well include them
"""
import csv
import sqlite3

import pkg_resources
import regex as re

from .miner import Miner
from .terms import *


# noinspection PyShadowingNames
class StatusMiner(Miner):
    """
    Customizations of Peter Kang & Wendy Chapman's statusminer.py algorithm.

    Output Terms with negation/possibility flags inherent in the term
    rather than words.
    Terms are sorted by relative position in the sentence.

    Changes from myNegTagger:
        1. Addition of history of tags.
        2. Each tag has choice of direction


    Overview of use:
        1. initialize with rules (grab from db with sortRulesFromTuples)
        2. call findNegation on the text, and hold onto the return
            Negation(Term) objects
        3. convert all other words in the text to some sort of Term
            objects
        4. call negateSentence(s) to determine which Terms are
            negated (and, optionally, which terms are possible)
    """

    '''
    Defining types of tags
    '''
    STOP_TAGS = ['conj']  # end of all scopes
    NEGATION_TAGS = ['affm', 'prob', 'poss', 'impr', 'negn', 'pseu']
    HYPOTHETICAL_TAGS = ['hypo', 'indi']
    TEMPORAL_TAGS = ['futp', 'hist']
    SUBJECT_TAGS = ['subj', 'othr']
    NEGEX_LEVEL = {
        0: [(0, '')
            ],
        1: [(12, '{1i+1d<3})'),
            (8, '{1i+1d<2})'),
            (0, '')
            ],
        2: [(14, '{1i+1d<4}'),
            (10, '{1i+1d<3}'),
            (6, '{1i+1d<2}'),
            (0, '')
            ],
        3: [(12, '{1i+1d<4}'),
            (8, '{1i+1d<3}'),
            (4, '{1i+1d<2}'),
            (0, '')
            ]
    }

    def __init__(self, rules=None, rx_var=0, maxscope=100, tablename='status1',
                 path=None):
        """
        Parameters:
            rules - list of negation trigger terms from the sortRules function
                if None, use built-in status
            rxVar - allowable regular expression variation
                    0: no variation; words must be exact => default
                    1: minimal variation
                    2: moderate variation
                    3: flexible
            maxscope - maximum distance allowed for negation/etc.
                DEFAULt is 100 (i.e., unlimited)
        """
        super().__init__()
        self._rules = []
        self._maxscope = maxscope
        if rules is None:
            if path:
                rules = self.load_negex_from_csv(path)
            elif tablename:
                rules = self.load_negex_from_db(tablename)
            else:  # tablename was explicitly negated
                rules = []
        self.add_rules(rules, rx_var)

    @staticmethod
    def load_negex_from_db(tablename):
        conn = sqlite3.connect(pkg_resources.resource_filename('pytakes.nlp', 'data/status.db'))
        cur = conn.cursor()
        cur.execute(f'select negex, type, direction from {tablename}')
        for negex, _type, direction in cur:
            yield negex, _type.strip('[]'), int(direction)

    @staticmethod
    def load_negex_from_csv(path):
        with open(path, newline='') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row['negex'], row['type'].strip('[]'), int(row['direction'])

    def add_rules(self, rules, rx_var):

        def get_negation_string(values, length):
            for x, y in values:
                if x > length:
                    return y
            return ''

        # add rules, but permit errors based on length
        for negex, _type, direction in self.sort_rules_for_status(rules):
            negex_pat = r'\b({})\b{}'.format(r'\W+'.join(negex.split()),
                                             get_negation_string(self.NEGEX_LEVEL[rx_var], len(negex)))
            self._rules.append((negex, re.compile(negex_pat, re.I), _type.strip('[]'), direction))

    @staticmethod
    def sort_rules_for_status(rulelist, exclusions=None):
        """
        Return sorted list of rules: (negex, type, direction, pattern)

        Input: list of tuples (negex, type, direction)

        Sorts list of rules descending based on length of rule,
        and converts the pattern into a regular expression.

        For use with myStatusTagger
        :param rulelist:
        :param exclusions:
        """
        sortedlist = []
        for negex, type_, direction in sorted(rulelist, key=lambda x: len(x[0]), reverse=True):
            if exclusions and negex in exclusions:
                continue
            sortedlist.append((negex, type_.strip('[]'), direction))
        return sortedlist

    def extract(self, terms):
        return []

    def mine(self, text, offset):
        """
        Find negations in a piece of text. If called sentence by
        sentence, set 'offset' to the len() of all previous
        sentences so that the Negation indices are correct.

        Parameters:
            text - piece of text to find negation
            offset - (default 0) len(all previous sentences)
                    if putting in only one sentence at a time
                    (not recommended as sentence boundaries
                    are not important for this portion of the
                    algorithm)
                    :return:
                    :param text:
                    :param offset:
        """
        negations = []
        # rules already sorted by length of negation expression
        for negex, pattern, _type, direction in self._rules:
            for m in pattern.finditer(text):
                n = Negation(negex, m.start(), m.end(), _type=_type, direction=direction, offset=offset)
                # longer sequences will trump smaller ones
                if n not in negations:
                    negations.append(n)
        return negations

    # noinspection PyPep8Naming
    def postprocess(self, terms):
        """
        :param terms:

        """
        # indices
        TYPE = 0
        STATUS = 1
        OVERLAP = 2
        COUNTER = 3

        def found_term(ind, _type):
            """ updates ind[icator] when a term is found
            :param ind:
            :param _type:
            """
            ind[TYPE] = _type
            ind[STATUS] = 1
            ind[OVERLAP] = 0
            ind[COUNTER] = 0

        def overlap_term(ind):
            """ updates ind[icator] when overlap found
            :param ind:
            """
            ind[OVERLAP] = 1

        def analyze_direction(sentence, directions):
            """
            directions - list of directions to look for
            1- backward
            2- forward
            3- both (bidirectional)
            :type sentence: list
            :param sentence:
            :param directions:
            """
            negtype = ['', 0, 0, 0]
            hypotype = ['', 0, 0, 0]
            temptype = ['', 0, 0, 0]
            subjtype = ['', 0, 0, 0]
            types = [negtype, hypotype, temptype, subjtype]
            for idx, term in enumerate(sentence):

                if term.direction() in directions:
                    if term.type() in self.NEGATION_TAGS:
                        found_term(negtype, term.type())
                    elif term.type() in self.HYPOTHETICAL_TAGS:
                        found_term(hypotype, term.type())
                    elif term.type() in self.TEMPORAL_TAGS:
                        found_term(temptype, term.type())
                    elif term.type() in self.SUBJECT_TAGS:
                        found_term(subjtype, term.type())

                elif term.type() in self.STOP_TAGS:
                    for _type in types:
                        overlap_term(_type)

                elif term.type() in self.NEGATION_TAGS:
                    overlap_term(negtype)

                elif term.type() in self.TEMPORAL_TAGS:
                    overlap_term(temptype)

                elif term.type() in self.HYPOTHETICAL_TAGS:
                    overlap_term(hypotype)

                elif term.type() in self.SUBJECT_TAGS:
                    overlap_term(subjtype)

                else:
                    for _type in types:
                        _type[COUNTER] += 1

                # check if term should be updated with any types
                for _type in types:
                    if _type[STATUS] == 1 and _type[OVERLAP] == 0 and _type[COUNTER] <= self._maxscope:
                        # ignoring affirmation tag (affm)
                        if _type[TYPE] == 'negn':
                            term.negate()
                        elif _type[TYPE] == 'impr':
                            term.improbable()
                        elif _type[TYPE] == 'poss':
                            term.possible()
                        elif _type[TYPE] == 'prob':
                            term.probable()
                        if _type[TYPE] == 'hypo':
                            term.hypothetical()
                        if _type[TYPE] == 'futp':
                            term.hypothetical()
                        if _type[TYPE] == 'hist':
                            term.historical()
                        if _type[TYPE] == 'othr':
                            term.other_subject()

            return sentence
            # end inner function

        # check all FORWARD (direction=2 or 3)
        sentence = analyze_direction(terms, [2, 3])

        # reverse and check all BACKWARD/BIDIRECTIONAL (1 or 3)      
        sentence.reverse()  # reverse sentence
        sentence = analyze_direction(terms, [1, 3])

        # put sentence back in correct order
        sentence.reverse()  # sentence correctly ordered

        return sentence

    def clean(self, text):
        return text
