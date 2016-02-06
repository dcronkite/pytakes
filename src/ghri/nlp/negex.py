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


def getNegex(dbi, neg_table):
    '''
    Retrieve negation triggers from table
    '''
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
             FROM %s
    ''' % neg_table)
    
def getContext(dbi, neg_table):
    '''
    Retrieve negation triggers from table.
    '''
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
                 , direction
             FROM %s
    ''' % neg_table)
    

def sortRulesForStatus( ruleList, exclusions=[] ):
    '''
    Return sorted list of rules: (negex, type, direction, pattern)
    
    Input: list of tuples (negex, type, direction)
    
    Sorts list of rules descending based on length of rule,
    and converts the pattern into a regular expression.
    
    For use with myStatusTagger
    '''
    ruleList.sort(key=lambda x:len(x[0]), reverse=True)
    sortedList = []
    for negex, type, direction in ruleList:
        if negex in exclusions: continue
        trig = r'\s+'.join(negex.split())
        pattern = re.compile(r'\b(' + trig + r')\b',re.I)
        sortedList.append( (negex,type,direction,pattern) )
    return sortedList
    

def sortRulesFromTuple (ruleList, exclusions=[]):
    """Return sorted list of rules.
    
    Input: list of tuples (negex, type).

    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule. """
    ruleList.sort(key=lambda x:len(x[0]),reverse=True)
    sortedList = []
    for negex,type in ruleList:
        if negex in exclusions: continue
        trig = r'\s+'.join(negex.split())
        pattern = re.compile(r'\b(' + trig + r')\b',re.I)
        sortedList.append( (negex,'',type,pattern) )
    return sortedList
    
    
def sortRules2 (ruleList):
    """Return sorted list of rules.
    
    ONLY ONE TAB REQUIRED!!!!
    
    Rules should be in a tab-delimited format: 'rule\t[four letter negation tag]'
    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule. """
    ruleList.sort(key = len, reverse = True)
    sortedList = []
    for s in ruleList:
        splitTrig = s[0].split()
        trig = r'\s+'.join(splitTrig)
        pattern = r'\b(' + trig + r')\b'
        sortedList.append( (s[0],'',s[1],re.compile(pattern, re.IGNORECASE)))
    return sortedList    

def sortRules (ruleList):
    """Return sorted list of rules.
    
    Rules should be in a tab-delimited format: 'rule\t\t[four letter negation tag]'
    Sorts list of rules descending based on length of the rule, 
    splits each rule into components, converts pattern to regular expression,
    and appends it to the end of the rule. """
    ruleList.sort(key = len, reverse = True)
    sortedList = []
    for rule in ruleList:
        s = rule.strip().split('\t')
        splitTrig = s[0].split()
        trig = r'\s+'.join(splitTrig)
        pattern = r'\b(' + trig + r')\b'
        s.append(re.compile(pattern, re.IGNORECASE))
        sortedList.append(s)
    return sortedList

class negTagger(object):
    '''Take a sentence and tag negation terms and negated phrases.
    
    Keyword arguments:
    sentence -- string to be tagged
    phrases  -- list of phrases to check for negation
    rules    -- list of negation trigger terms from the sortRules function
    negP     -- tag 'possible' terms as well (default = True)    '''
    def __init__(self, sentence = '', phrases = None, rules = None, 
                 negP = True):
        self.__sentence = sentence
        self.__phrases = phrases
        self.__rules = rules
        self.__negTaggedSentence = ''
        self.__scopesToReturn = []
        self.__negationFlag = None
        
        filler = '_'
        
        for rule in self.__rules:
            reformatRule = re.sub(r'\s+', filler, rule[0].strip())
            self.__sentence = rule[3].sub (' ' + rule[2].strip()
                                                          + reformatRule
                                                          + rule[2].strip() + ' ', self.__sentence)
        for phrase in self.__phrases:
            phrase = re.sub(r'([.^$*+?{\\|()[\]])', r'\\\1', phrase) # prep for conversion to regex
            splitPhrase = phrase.split()
            joiner = r'\W+'
            joinedPattern = r'\b' + joiner.join(splitPhrase) +  r'\b'
            reP = re.compile(joinedPattern, re.IGNORECASE)
            m = reP.search(self.__sentence)
            if m:
                self.__sentence = self.__sentence.replace(m.group(0), '[PHRASE]'
                                                          + re.sub(r'\s+', filler, m.group(0).strip())
                                                          + '[PHRASE]')
    
#        Exchanges the [PHRASE] ... [PHRASE] tags for [NEGATED] ... [NEGATED] 
#        based on PREN, POST rules and if negPoss is set to True then based on 
#        PREP and POSP, as well.
#        Because PRENEGATION [PREN} is checked first it takes precedent over
#        POSTNEGATION [POST]. Similarly POSTNEGATION [POST] takes precedent over
#        POSSIBLE PRENEGATION [PREP] and [PREP] takes precedent over POSSIBLE 
#        POSTNEGATION [POSP].
              
        overlapFlag = 0
        prenFlag = 0
        postFlag = 0
        prePossibleFlag = 0
        postPossibleFlag = 0
        
        sentenceTokens = self.__sentence.split()
        sentencePortion = ''
        aScopes = []
        sb = []
        #check for [PREN]
        for i in range(len(sentenceTokens)):
            if sentenceTokens[i][:6] == '[PREN]':
                prenFlag = 1
                overlapFlag = 0

            if sentenceTokens[i][:6] in ['[CONJ]', '[PSEU]', '[POST]', '[PREP]', '[POSP]']:
                overlapFlag = 1
            
            if i+1 < len(sentenceTokens):
                if sentenceTokens[i+1][:6] == '[PREN]':
                    overlapFlag = 1
                    if sentencePortion.strip():
                        aScopes.append(sentencePortion.strip())
                    sentencePortion = ''
            
            if prenFlag == 1 and overlapFlag == 0:
                sentenceTokens[i] = sentenceTokens[i].replace('[PHRASE]', '[NEGATED]')
                sentencePortion = sentencePortion + ' ' + sentenceTokens[i]
            
            sb.append(sentenceTokens[i])
        
        if sentencePortion.strip():
            aScopes.append(sentencePortion.strip())
        
        sentencePortion = ''
        sb.reverse()
        sentenceTokens = sb
        sb2 = []
        # Check for [POST]
        for i in range(len(sentenceTokens)):
            if sentenceTokens[i][:6] == '[POST]':
                postFlag = 1
                overlapFlag = 0

            if sentenceTokens[i][:6] in ['[CONJ]', '[PSEU]', '[PREN]', '[PREP]', '[POSP]']:
                overlapFlag = 1
            
            if i+1 < len(sentenceTokens):
                if sentenceTokens[i+1][:6] == '[POST]':
                    overlapFlag = 1
                    if sentencePortion.strip():
                        aScopes.append(sentencePortion.strip())
                    sentencePortion = ''
            
            if postFlag == 1 and overlapFlag == 0:
                sentenceTokens[i] = sentenceTokens[i].replace('[PHRASE]', '[NEGATED]')
                sentencePortion = sentenceTokens[i] + ' ' + sentencePortion
            
            sb2.insert(0, sentenceTokens[i])
        
        if sentencePortion.strip():
            aScopes.append(sentencePortion.strip())
        
        sentencePortion = ''
        self.__negTaggedSentence = ' '.join(sb2)
        
        if negP:
            sentenceTokens = sb2
            sb3 = []
            # Check for [PREP]
            for i in range(len(sentenceTokens)):
                if sentenceTokens[i][:6] == '[PREP]':
                    prePossibleFlag = 1
                    overlapFlag = 0

                if sentenceTokens[i][:6] in ['[CONJ]', '[PSEU]', '[POST]', '[PREN]', '[POSP]']:
                    overlapFlag = 1
            
                if i+1 < len(sentenceTokens):
                    if sentenceTokens[i+1][:6] == '[PREP]':
                        overlapFlag = 1
                        if sentencePortion.strip():
                            aScopes.append(sentencePortion.strip())
                        sentencePortion = ''
            
                if prePossibleFlag == 1 and overlapFlag == 0:
                    sentenceTokens[i] = sentenceTokens[i].replace('[PHRASE]', '[POSSIBLE]')
                    sentencePortion = sentencePortion + ' ' + sentenceTokens[i]
            
                sb3 = sb3 + ' ' + sentenceTokens[i]
        
            if sentencePortion.strip():
                aScopes.append(sentencePortion.strip())
            
            sentencePortion = ''
            sb3.reverse()
            sentenceTokens = sb3 
            sb4 = []
            # Check for [POSP]
            for i in range(len(sentenceTokens)):
                if sentenceTokens[i][:6] == '[POSP]':
                    postPossibleFlag = 1
                    overlapFlag = 0

                if sentenceTokens[i][:6] in ['[CONJ]', '[PSEU]', '[PREN]', '[PREP]', '[POST]']:
                    overlapFlag = 1
            
                if i+1 < len(sentenceTokens):
                    if sentenceTokens[i+1][:6] == '[POSP]':
                        overlapFlag = 1
                        if sentencePortion.strip():
                            aScopes.append(sentencePortion.strip())
                        sentencePortion = ''
            
                if postPossibleFlag == 1 and overlapFlag == 0:
                    sentenceTokens[i] = sentenceTokens[i].replace('[PHRASE]', '[POSSIBLE]')
                    sentencePortion = sentenceTokens[i] + ' ' + sentencePortion
            
                sb4.insert(0, sentenceTokens[i])
        
            if sentencePortion.strip():
                aScopes.append(sentencePortion.strip())
            
            self.__negTaggedSentence = ' '.join(sb4)
            
        if '[NEGATED]' in self.__negTaggedSentence:
            self.__negationFlag = 'negated'
        elif '[POSSIBLE]' in self.__negTaggedSentence:
            self.__negationFlag = 'possible'
        else:
            self.__negationFlag = 'affirmed'
        
        self.__negTaggedSentence = self.__negTaggedSentence.replace(filler, ' ')
        
        for line in aScopes:
            tokensToReturn = []
            thisLineTokens = line.split()
            for token in thisLineTokens:
                if token[:6] not in ['[PREN]', '[PREP]', '[POST]', '[POSP]']:
                    tokensToReturn.append(token)
            self.__scopesToReturn.append(' '.join(tokensToReturn))

    def getNegTaggedSentence(self):
        return self.__negTaggedSentence
    def getNegationFlag(self):
        return self.__negationFlag
    def getScopes(self):
        return self.__scopesToReturn
    def isNegated(self):
        return self.__negationFlag == 'negated'
    def isAffirmed(self):
        return self.__negationFlag == 'affirmed'
    
    def __str__(self):
        text = self.__negTaggedSentence
        text += '\t' + self.__negationFlag
        text += '\t' + '\t'.join(self.__scopesToReturn)
        return text
        
        
class myNegTagger(object):
    '''
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
    '''
    
    def __init__(self,rules,negP=True, rxVar=0):
        '''
        Parameters:
            rules - list of negation trigger terms from the sortRules function
            negP - tag 'possible' terms as well (default = True)
            rxVar - allowable regular expression variation
                    0: no variation; words must be exact
                    1: minimal variation
                    2: moderate variation
                    3: flexible    
        '''
        self.__rules = []
        # add rules, but permit errors based on length
        for negex,_,type,pattern in rules:
            
            # improve this bit, in order to allow variations
            # enforce first letter of words?
            if len(negex) > 12:
                self.__rules.append( 
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) 
                                    + '\b{1i+1d<4})', re.V1|re.I),
                     type[1:5]))
            elif len(negex) > 8:
                self.__rules.append( 
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) 
                                    + '\b{1i+1d<3})', re.V1|re.I),
                     type[1:5]))
            elif len(negex) > 4:
                self.__rules.append( 
                    (negex,
                     re.compile('(\b' + r'\s+'.join(negex.split()) 
                                    + '\b{1i+1d<2})', re.V1|re.I),
                     type[1:5]))
            else: # less than 4
                self.__rules.append( (negex,pattern,type[1:5]) )
        
        self.negP = negP
        
    def findNegation(self,text,offset=0):
        '''
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
        '''
        negations = []
        # rules already sorted by length of negation expression
        for negex,pattern,type in self.__rules:
            for m in pattern.finditer(text):
                n = Negation(negex,m.start()+offset,m.end()+offset,type=type)
                # longer sequences will trump smaller ones
                if n not in negations:
                    negations.append(n)
        return negations
        
    def negateSentences(self, sentences):
        new_sentences = []
        for sentence in sentences:
            new_sentences += self.negateSentence(sentence)
        return new_sentences
        
    def negateSentence(self, sentence):
        overlapFlag = 0
        prenFlag = 0
        postFlag = 0
        prePossibleFlag = 0
        postPossibleFlag = 0
        # check for PREN
        counter = 0 # limit scope of prenegation
        for idx,term in enumerate(sentence):
            if term.type() == 'pren':
                prenFlag = 1
                overlapFlag = 0
                counter = 0
            
            elif term.type() in ['conj','pseu','post','prep','posp']:
                overlapFlag = 1
                
            elif term.type() == 'phrasebreak': #include commas (NYI)
                prenFlag = 0
                
            else:
                counter += 1
                
            if idx+1 < len(sentence):
                if sentence[idx+1].type() == 'pren':
                    overlapFlag = 1
            
            # if prenFlag == 1 and overlapFlag == 0:
                # print counter,term
            if prenFlag == 1 and overlapFlag == 0 and counter <= 5:
                # print " >>NEGATE!"
                term.negate()
        #check for POST        
        sentence.reverse() # reverse sentence
        for idx,term in enumerate(sentence):
            if term.type() == 'post':
                postFlag = 1
                overlapFlag = 0
            
            elif term.type() in ['conj','pseu','pren','prep','posp']:
                overlapFlag = 1
                
            if idx+1 < len(sentence):
                if sentence[idx+1].type() == 'post':
                    overlapFlag = 1
            
            if postFlag == 1 and overlapFlag == 0:
                term.negate()
        
        if self.negP: # check POSSIBILITY
            # check for PREP (sentence is still reversed)
            for idx,term in enumerate(sentence):
                if term.type() == 'prep':
                    prePossibleFlag = 1
                    overlapFlag = 0
                
                elif term.type() in ['conj','pseu','post','pren','posp']:
                    overlapFlag = 1
                    
                if idx+1 < len(sentence):
                    if sentence[idx+1].type() == 'prep':
                        overlapFlag = 1
                
                if prePossibleFlag == 1 and overlapFlag == 0:
                    term.possible()
            # check for POSP
            sentence.reverse() # sentence correctly ordered
            for idx,term in enumerate(sentence):
                if term.type() == 'posp':
                    postPossibleFlag = 1
                    overlapFlag = 0
                
                elif term.type() in ['conj','pseu','post','pren','prep']:
                    overlapFlag = 1
                    
                if idx+1 < len(sentence):
                    if sentence[idx+1].type() == 'posp':
                        overlapFlag = 1
                
                if postPossibleFlag == 1 and overlapFlag == 0:
                    term.possible()
        
        return sentence
    
    
class myStatusTagger(object):
    '''
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
    '''
    
    '''
    Defining types of tags
    '''
    STOP_TAGS = ['conj'] # end of all scopes
    NEGATION_TAGS = ['affm','prob','poss','impr', 'negn', 'pseu']
    HYPOTHETICAL_TAGS = ['hypo', 'indi']
    TEMPORAL_TAGS = ['futp', 'hist']
    SUBJECT_TAGS = ['subj', 'othr']
    
    
    def __init__(self,rules, rxVar=0, maxscope=100):
        '''
        Parameters:
            rules - list of negation trigger terms from the sortRules function
            rxVar - allowable regular expression variation
                    0: no variation; words must be exact => default
                    1: minimal variation
                    2: moderate variation
                    3: flexible    
            maxscope - maximum distance allowed for negation/etc.
                DEFAULt is 100 (i.e., unlimited)
        '''
        self.__rules = []
        self.maxscope_ = maxscope
        
        # add rules, but permit errors based on length
        for negex,type,direction,pattern in rules:
            
            if rxVar == 0: # no variation
                self.__rules.append( (negex, pattern, type[1:5], direction) )
                
            #minimal variation in negation
            elif rxVar == 1: #minimal variation
                if len(negex) > 12:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<3})', re.V1|re.I),
                         type[1:5],
                         direction))
                elif len(negex) > 8:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<2})', re.V1|re.I),
                         type[1:5],
                         direction))
                else: # less than 4
                    self.__rules.append( (negex,pattern,type[1:5], direction) )
                    
            # allow moderate variation in negation
            elif rxVar == 2: # moderate variation
                if len(negex) > 14:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<4})', re.V1|re.I),
                         type[1:5],
                         direction))
                elif len(negex) > 10:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<3})', re.V1|re.I),
                         type[1:5],
                         direction))
                elif len(negex) > 6:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<2})', re.V1|re.I),
                         type[1:5],
                         direction))
                else: # less than 4
                    self.__rules.append( (negex,pattern,type[1:5]) )
                         
            # very flexible negation          
            elif rxVar >= 3: # very flexible
                if len(negex) > 12:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<4})', re.V1|re.I),
                         type[1:5],
                         direction))
                elif len(negex) > 8:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<3})', re.V1|re.I),
                         type[1:5],
                         direction))
                elif len(negex) > 4:
                    self.__rules.append( 
                        (negex,
                         re.compile(r'(\b' + r'\s+'.join(negex.split()) 
                                        + r'\b{1i+1d<2})', re.V1|re.I),
                         type[1:5],
                         direction))
                else: # less than 4
                    self.__rules.append( (negex,pattern,type[1:5], direction) )
                    
        
    def findNegation(self,text,offset=0):
        '''
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
        '''
        negations = []
        # rules already sorted by length of negation expression
        for negex,pattern,type,direction in self.__rules:
            for m in pattern.finditer(text):
                n = Negation(negex,m.start()+offset,m.end()+offset,type=type,direction=direction)
                # longer sequences will trump smaller ones
                if n not in negations:
                    negations.append(n)
        return negations
        
    def analyzeSentences(self, sentences):
        new_sentences = []
        for sentence in sentences:
            new_sentences += self.analyzeSentence(sentence)
        return new_sentences
        
        
    def analyzeSentence(self, sentence):
        '''
        
        '''
        #indices
        TYPE = 0
        STATUS = 1
        OVERLAP = 2
        COUNTER = 3
        
                
        def found_term(ind, type):
            ''' updates ind[icator] when a term is found '''
            ind[TYPE] = type
            ind[STATUS] = 1
            ind[OVERLAP] = 0
            ind[COUNTER] = 0
            
        def overlap_term(ind):
            ''' updates ind[icator] when overlap found '''
            ind[OVERLAP] = 1
            
            
        def analyzeDirection( sentence, directions ):
            '''
            directions - list of directions to look for
            1- backward
            2- forward
            3- both (bidirectional)
            '''
            negType = ['', 0, 0, 0]
            hypoType = ['', 0, 0, 0]
            tempType = ['', 0, 0, 0]
            subjType = ['', 0, 0, 0]
            types = [negType, hypoType, tempType, subjType]
            for idx,term in enumerate(sentence):
                
                if term.direction() in directions:
                    if term.type() in self.NEGATION_TAGS: found_term(negType, term.type())
                    elif term.type() in self.HYPOTHETICAL_TAGS: found_term(hypoType, term.type())
                    elif term.type() in self.TEMPORAL_TAGS: found_term(tempType, term.type())
                    elif term.type() in self.SUBJECT_TAGS: found_term(subjType, term.type())
                    
                elif term.type() == self.STOP_TAGS:
                    for type in types: overlap_term(type)
                
                elif term.type() in self.NEGATION_TAGS:
                    overlap_term(negType)
                    
                elif term.type() in self.TEMPORAL_TAGS:
                    overlap_term(tempType)
                    
                elif term.type() in self.HYPOTHETICAL_TAGS:
                    overlap_term(hypoType)
                    
                elif term.type() in self.SUBJECT_TAGS:
                    overlap_term(subjType)
                    
                else:
                    for type in types:
                        type[COUNTER] += 1
    
                # check if term should be updated with any types
                for type in types:
                    if type[STATUS] == 1 and type[OVERLAP] == 0 and type[COUNTER] <= self.maxscope_:
                        # ignoring affirmation tag (affm)
                        if type[TYPE] == 'negn':
                            term.negate()
                        elif type[TYPE] == 'impr':
                            term.improbable()
                        elif type[TYPE] == 'poss':
                            term.possible()
                        elif type[TYPE] == 'prob':
                            term.probable()
                        if type[TYPE] == 'hypo':
                            term.hypothetical()
                        if type[TYPE] == 'futp':
                            term.hypothetical()
                        if type[TYPE] == 'hist':
                            term.historical()
                        if type[TYPE] == 'othr':
                            term.other_subject()
                            
            return sentence
            # end inner function
        
        # check all FORWARD (direction=2 or 3)
        sentence = analyzeDirection(sentence, [2, 3])

        # reverse and check all BACKWARD/BIDIRECTIONAL (1 or 3)      
        sentence.reverse() # reverse sentence
        sentence = analyzeDirection(sentence, [1, 3])

        # put sentence back in correct order
        sentence.reverse() # sentence correctly ordered
        
        return sentence