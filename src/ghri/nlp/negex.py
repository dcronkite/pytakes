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

import regex as re
from .terms import *


def get_negex(dbi, neg_table):
    """
    Retrieve negation triggers from table
    :param dbi:
    :param neg_table:
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
             FROM %s
    ''' % neg_table)


def get_context(dbi, neg_table):
    """
    Retrieve negation triggers from table.
    :param dbi:
    :param neg_table:
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
                 , direction
             FROM %s
    ''' % neg_table)


def sort_rules_for_status(rulelist, exclusions=[]):
    """
    Return sorted list of rules: (negex, type, direction, pattern)

    Input: list of tuples (negex, type, direction)

    Sorts list of rules descending based on length of rule,
    and converts the pattern into a regular expression.

    For use with myStatusTagger
    :param rulelist:
    :param exclusions:
    """
    rulelist.sort(key=lambda x: len(x[0]), reverse=True)
    sortedlist = []
    for negex, type_, direction in rulelist:
        if negex in exclusions: continue
        trig = r'\s+'.join(negex.split())
        pattern = re.compile(r'\b(' + trig + r')\b', re.I)
        sortedlist.append((negex, type_, direction, pattern))
    return sortedlist


def sort_rules_from_tuple(rulelist, exclusions=[]):
    """Return sorted list of rules.
    
    Input: list of tuples (negex, type).

    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule.
    :param rulelist:
    :param exclusions: """
    rulelist.sort(key=lambda x: len(x[0]), reverse=True)
    sortedlist = []
    for negex, _type in rulelist:
        if negex in exclusions:
            continue
        trig = r'\s+'.join(negex.split())
        pattern = re.compile(r'\b(' + trig + r')\b', re.I)
        sortedlist.append((negex, '', _type, pattern))
    return sortedlist


def sort_rules2(rulelist):
    """Return sorted list of rules.
    
    ONLY ONE TAB REQUIRED!!!!
    
    Rules should be in a tab-delimited format: 'rule\t[four letter negation tag]'
    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule.
    :param rulelist: """
    rulelist.sort(key=len, reverse=True)
    sortedlist = []
    for s in rulelist:
        splittrig = s[0].split()
        trig = r'\s+'.join(splittrig)
        pattern = r'\b(' + trig + r')\b'
        sortedlist.append((s[0], '', s[1], re.compile(pattern, re.IGNORECASE)))
    return sortedlist


def sort_rules(rulelist):
    """Return sorted list of rules.
    
    Rules should be in a tab-delimited format: 'rule\t\t[four letter negation tag]'
    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule.
    :param rulelist: """
    rulelist.sort(key=len, reverse=True)
    sortedlist = []
    for rule in rulelist:
        s = rule.strip().split('\t')
        splittrig = s[0].split()
        trig = r'\s+'.join(splittrig)
        pattern = r'\b(' + trig + r')\b'
        s.append(re.compile(pattern, re.IGNORECASE))
        sortedlist.append(s)
    return sortedlist


class NegTagger(object):
    """Take a sentence and tag negation terms and negated phrases.

    Keyword arguments:
    sentence -- string to be tagged
    phrases  -- list of phrases to check for negation
    rules    -- list of negation trigger terms from the sortRules function
    negP     -- tag 'possible' terms as well (default = True)    """

    def __init__(self, sentence='', phrases=None, rules=None,
                 neg_p=True):
        self.__sentence = sentence
        self.__phrases = phrases
        self.__rules = rules
        self.__negTaggedSentence = ''
        self.__scopesToReturn = []
        self.__negationFlag = None

        filler = '_'

        for rule in self.__rules:
            reformatrule = re.sub(r'\s+', filler, rule[0].strip())
            self.__sentence = rule[3].sub(' ' + rule[2].strip() + reformatrule + rule[2].strip() + ' ', self.__sentence)
        for phrase in self.__phrases:
            phrase = re.sub(r'([.^$*+?{\\|()[\]])', r'\\\1', phrase)  # prep for conversion to regex
            splitphrase = phrase.split()
            joiner = r'\W+'
            joinedpattern = r'\b' + joiner.join(splitphrase) + r'\b'
            re_p = re.compile(joinedpattern, re.IGNORECASE)
            m = re_p.search(self.__sentence)
            if m:
                self.__sentence = self.__sentence.replace(m.group(0), '[PHRASE]' + re.sub(r'\s+', filler, m.group(
                    0).strip()) + '[PHRASE]')

                #        Exchanges the [PHRASE] ... [PHRASE] tags for [NEGATED] ... [NEGATED]
                #        based on PREN, POST rules and if negPoss is set to True then based on
                #        PREP and POSP, as well.
                #        Because PRENEGATION [PREN} is checked first it takes precedent over
                #        POSTNEGATION [POST]. Similarly POSTNEGATION [POST] takes precedent over
                #        POSSIBLE PRENEGATION [PREP] and [PREP] takes precedent over POSSIBLE
                #        POSTNEGATION [POSP].

        overlapflag = 0
        prenflag = 0
        postflag = 0
        prepossibleflag = 0
        postpossibleflag = 0

        sentencetokens = self.__sentence.split()
        sentenceportion = ''
        a_scopes = []
        sb = []
        # check for [PREN]
        for i in range(len(sentencetokens)):
            if sentencetokens[i][:6] == '[PREN]':
                prenflag = 1
                overlapflag = 0

            if sentencetokens[i][:6] in ['[CONJ]', '[PSEU]', '[POST]', '[PREP]', '[POSP]']:
                overlapflag = 1

            if i + 1 < len(sentencetokens):
                if sentencetokens[i + 1][:6] == '[PREN]':
                    overlapflag = 1
                    if sentenceportion.strip():
                        a_scopes.append(sentenceportion.strip())
                    sentenceportion = ''

            if prenflag == 1 and overlapflag == 0:
                sentencetokens[i] = sentencetokens[i].replace('[PHRASE]', '[NEGATED]')
                sentenceportion = sentenceportion + ' ' + sentencetokens[i]

            sb.append(sentencetokens[i])

        if sentenceportion.strip():
            a_scopes.append(sentenceportion.strip())

        sentenceportion = ''
        sb.reverse()
        sentencetokens = sb
        sb2 = []
        # Check for [POST]
        for i in range(len(sentencetokens)):
            if sentencetokens[i][:6] == '[POST]':
                postflag = 1
                overlapflag = 0

            if sentencetokens[i][:6] in ['[CONJ]', '[PSEU]', '[PREN]', '[PREP]', '[POSP]']:
                overlapflag = 1

            if i + 1 < len(sentencetokens):
                if sentencetokens[i + 1][:6] == '[POST]':
                    overlapflag = 1
                    if sentenceportion.strip():
                        a_scopes.append(sentenceportion.strip())
                    sentenceportion = ''

            if postflag == 1 and overlapflag == 0:
                sentencetokens[i] = sentencetokens[i].replace('[PHRASE]', '[NEGATED]')
                sentenceportion = sentencetokens[i] + ' ' + sentenceportion

            sb2.insert(0, sentencetokens[i])

        if sentenceportion.strip():
            a_scopes.append(sentenceportion.strip())

        sentenceportion = ''
        self.__negTaggedSentence = ' '.join(sb2)

        if neg_p:
            sentencetokens = sb2
            sb3 = []
            # Check for [PREP]
            for i in range(len(sentencetokens)):
                if sentencetokens[i][:6] == '[PREP]':
                    prepossibleflag = 1
                    overlapflag = 0

                if sentencetokens[i][:6] in ['[CONJ]', '[PSEU]', '[POST]', '[PREN]', '[POSP]']:
                    overlapflag = 1

                if i + 1 < len(sentencetokens):
                    if sentencetokens[i + 1][:6] == '[PREP]':
                        overlapflag = 1
                        if sentenceportion.strip():
                            a_scopes.append(sentenceportion.strip())
                        sentenceportion = ''

                if prepossibleflag == 1 and overlapflag == 0:
                    sentencetokens[i] = sentencetokens[i].replace('[PHRASE]', '[POSSIBLE]')
                    sentenceportion = sentenceportion + ' ' + sentencetokens[i]

                sb3 = sb3 + ' ' + sentencetokens[i]

            if sentenceportion.strip():
                a_scopes.append(sentenceportion.strip())

            sentenceportion = ''
            sb3.reverse()
            sentencetokens = sb3
            sb4 = []
            # Check for [POSP]
            for i in range(len(sentencetokens)):
                if sentencetokens[i][:6] == '[POSP]':
                    postpossibleflag = 1
                    overlapflag = 0

                if sentencetokens[i][:6] in ['[CONJ]', '[PSEU]', '[PREN]', '[PREP]', '[POST]']:
                    overlapflag = 1

                if i + 1 < len(sentencetokens):
                    if sentencetokens[i + 1][:6] == '[POSP]':
                        overlapflag = 1
                        if sentenceportion.strip():
                            a_scopes.append(sentenceportion.strip())
                        sentenceportion = ''

                if postpossibleflag == 1 and overlapflag == 0:
                    sentencetokens[i] = sentencetokens[i].replace('[PHRASE]', '[POSSIBLE]')
                    sentenceportion = sentencetokens[i] + ' ' + sentenceportion

                sb4.insert(0, sentencetokens[i])

            if sentenceportion.strip():
                a_scopes.append(sentenceportion.strip())

            self.__negTaggedSentence = ' '.join(sb4)

        if '[NEGATED]' in self.__negTaggedSentence:
            self.__negationFlag = 'negated'
        elif '[POSSIBLE]' in self.__negTaggedSentence:
            self.__negationFlag = 'possible'
        else:
            self.__negationFlag = 'affirmed'

        self.__negTaggedSentence = self.__negTaggedSentence.replace(filler, ' ')

        for line in a_scopes:
            tokenstoreturn = []
            thislinetokens = line.split()
            for token in thislinetokens:
                if token[:6] not in ['[PREN]', '[PREP]', '[POST]', '[POSP]']:
                    tokenstoreturn.append(token)
            self.__scopesToReturn.append(' '.join(tokenstoreturn))

    def get_neg_tagged_sentence(self):
        return self.__negTaggedSentence

    def get_negation_flag(self):
        return self.__negationFlag

    def get_scopes(self):
        return self.__scopesToReturn

    def is_negated(self):
        return self.__negationFlag == 'negated'

    def is_affirmed(self):
        return self.__negationFlag == 'affirmed'

    def __str__(self):
        text = self.__negTaggedSentence
        text += '\t' + self.__negationFlag
        text += '\t' + '\t'.join(self.__scopesToReturn)
        return text


class MyNegTagger(object):
    """
    Customizations of Peter Kang & Wendy Chapman's negex.py algorithm.

    Output Terms with negation/possibility flags inherent in the term
    rather than words.
    Terms are sorted by relative position in the sentence.

    Overview of use:
        1. initialize with rules (grab from db with sortRulesFromTuples)
        2. call findNegation on the text, and hold onto the return
            Negation(Term) objects
        3. convert all other words in the text to some sort of Term
            objects
        4. call negateSentence(s) to determine which Terms are
            negated (and, optionally, which terms are possible)
    """

    def __init__(self, rules, neg_p=True, rx_var=0):
        """
        Parameters:
            rules - list of negation trigger terms from the sortRules function
            negP - tag 'possible' terms as well (default = True)
            rxVar - allowable regular expression variation
                    0: no variation; words must be exact
                    1: minimal variation
                    2: moderate variation
                    3: flexible
        """
        self.__rules = []
        # add rules, but permit errors based on length
        for negex, _, _type, pattern in rules:

            # improve this bit, in order to allow variations
            # enforce first letter of words?
            if len(negex) > 12:
                self.__rules.append(
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) + '\b{1i+1d<4})', re.V1 | re.I),
                     _type[1:5]))
            elif len(negex) > 8:
                self.__rules.append(
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) + '\b{1i+1d<3})', re.V1 | re.I),
                     _type[1:5]))
            elif len(negex) > 4:
                self.__rules.append(
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) + '\b{1i+1d<2})', re.V1 | re.I),
                     _type[1:5]))
            else:  # less than 4
                self.__rules.append((negex, pattern, _type[1:5]))

        self.negP = neg_p

    def find_negation(self, text, offset=0):
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
                    :param text:
                    :param offset:
        """
        negations = []
        # rules already sorted by length of negation expression
        for negex, pattern, _type in self.__rules:
            for m in pattern.finditer(text):
                n = Negation(negex, m.start() + offset, m.end() + offset, _type=_type)
                # longer sequences will trump smaller ones
                if n not in negations:
                    negations.append(n)
        return negations

    def negate_sentences(self, sentences):
        new_sentences = []
        for sentence in sentences:
            new_sentences += self.negate_sentence(sentence)
        return new_sentences

    def negate_sentence(self, sentence):
        overlapflag = 0
        prenflag = 0
        postflag = 0
        prepossibleflag = 0
        postpossibleflag = 0
        # check for PREN
        counter = 0  # limit scope of prenegation
        for idx, term in enumerate(sentence):
            if term.type() == 'pren':
                prenflag = 1
                overlapflag = 0
                counter = 0

            elif term.type() in ['conj', 'pseu', 'post', 'prep', 'posp']:
                overlapflag = 1

            elif term.type() == 'phrasebreak':  # include commas (NYI)
                prenflag = 0

            else:
                counter += 1

            if idx + 1 < len(sentence):
                if sentence[idx + 1].type() == 'pren':
                    overlapflag = 1

            if prenflag == 1 and overlapflag == 0 and counter <= 5:
                term.negate()
        # check for POST
        sentence.reverse()  # reverse sentence
        for idx, term in enumerate(sentence):
            if term.type() == 'post':
                postflag = 1
                overlapflag = 0

            elif term.type() in ['conj', 'pseu', 'pren', 'prep', 'posp']:
                overlapflag = 1

            if idx + 1 < len(sentence):
                if sentence[idx + 1].type() == 'post':
                    overlapflag = 1

            if postflag == 1 and overlapflag == 0:
                term.negate()

        if self.negP:  # check POSSIBILITY
            # check for PREP (sentence is still reversed)
            for idx, term in enumerate(sentence):
                if term.type() == 'prep':
                    prepossibleflag = 1
                    overlapflag = 0

                elif term.type() in ['conj', 'pseu', 'post', 'pren', 'posp']:
                    overlapflag = 1

                if idx + 1 < len(sentence):
                    if sentence[idx + 1].type() == 'prep':
                        overlapflag = 1

                if prepossibleflag == 1 and overlapflag == 0:
                    term.possible()
            # check for POSP
            sentence.reverse()  # sentence correctly ordered
            for idx, term in enumerate(sentence):
                if term.type() == 'posp':
                    postpossibleflag = 1
                    overlapflag = 0

                elif term.type() in ['conj', 'pseu', 'post', 'pren', 'prep']:
                    overlapflag = 1

                if idx + 1 < len(sentence):
                    if sentence[idx + 1].type() == 'posp':
                        overlapflag = 1

                if postpossibleflag == 1 and overlapflag == 0:
                    term.possible()

        return sentence


# noinspection PyShadowingNames
class MyStatusTagger(object):
    """
    Customizations of Peter Kang & Wendy Chapman's negex.py algorithm.

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

    def __init__(self, rules, rx_var=0, maxscope=100):
        """
        Parameters:
            rules - list of negation trigger terms from the sortRules function
            rxVar - allowable regular expression variation
                    0: no variation; words must be exact => default
                    1: minimal variation
                    2: moderate variation
                    3: flexible
            maxscope - maximum distance allowed for negation/etc.
                DEFAULt is 100 (i.e., unlimited)
        """
        self.__rules = []
        self.maxscope_ = maxscope

        # add rules, but permit errors based on length
        for negex, _type, direction, pattern in rules:

            if rx_var == 0:  # no variation
                self.__rules.append((negex, pattern, _type[1:5], direction))

            # minimal variation in negation
            elif rx_var == 1:  # minimal variation
                if len(negex) > 12:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<3})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                elif len(negex) > 8:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<2})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                else:  # less than 4
                    self.__rules.append((negex, pattern, _type[1:5], direction))

            # allow moderate variation in negation
            elif rx_var == 2:  # moderate variation
                if len(negex) > 14:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<4})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                elif len(negex) > 10:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<3})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                elif len(negex) > 6:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<2})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                else:  # less than 4
                    self.__rules.append((negex, pattern, _type[1:5]))

            # very flexible negation          
            elif rx_var >= 3:  # very flexible
                if len(negex) > 12:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<4})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                elif len(negex) > 8:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<3})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                elif len(negex) > 4:
                    self.__rules.append(
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) + r'\b{1i+1d<2})', re.V1 | re.I),
                         _type[1:5],
                         direction))
                else:  # less than 4
                    self.__rules.append((negex, pattern, _type[1:5], direction))

    def find_negation(self, text, offset=0):
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
        for negex, pattern, _type, direction in self.__rules:
            for m in pattern.finditer(text):
                n = Negation(negex, m.start() + offset, m.end() + offset, _type=_type, direction=direction)
                # longer sequences will trump smaller ones
                if n not in negations:
                    negations.append(n)
        return negations

    def analyze_sentences(self, sentences):
        new_sentences = []
        for sentence in sentences:
            new_sentences += self.analyze_sentence(sentence)
        return new_sentences

    # noinspection PyPep8Naming
    def analyze_sentence(self, sentence):
        """
        :param sentence:

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

                elif term.type() == self.STOP_TAGS:
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
                    if _type[STATUS] == 1 and _type[OVERLAP] == 0 and _type[COUNTER] <= self.maxscope_:
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
        sentence = analyze_direction(sentence, [2, 3])

        # reverse and check all BACKWARD/BIDIRECTIONAL (1 or 3)      
        sentence.reverse()  # reverse sentence
        sentence = analyze_direction(sentence, [1, 3])

        # put sentence back in correct order
        sentence.reverse()  # sentence correctly ordered

        return sentence
