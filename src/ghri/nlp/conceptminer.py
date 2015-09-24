'''
ghri.wildcat.conceptminer.py
    created: 2013-04-18
    
Purpose:
    Mine concepts from the text. Essentially do what cTAKES does,
    but do it better AND simpler.
    
Author:
    Cronkite, David (GHRI)
    
Edits:
2013-11-05    added possible tags
2013-11-26    replaced by conceptminer2 for additional assertion annotation

'''
import copy
import string
import numbers

import convert
from negex import *


def remove_punct(text):
    return re.sub(ur'\p{P}+','',text)
    
    
class ConceptMiner(object):
    
    def __init__(self, id_term_cat_val_rxVar_wdOrder, rxVar=0):
        self.cid_to_cat = {} # ConceptID -> category
        self.cid_to_tids = {} # ConceptID to TermIDs
        self.wordID = 0
        self.tid_to_tid = {} # list of conversions of
                             # new TermIDs to old TermIDs
                             # this should be a one-to-many
                             # relationship where one New
                             # TermID is equivalent to several
                             # older TermIDs
                             # no reason to have it the other
                             # way around
        self.cid_to_val = {}
        self.cid_word_order = {} # word order constraints
        self.wordlist = []
        
        
        self._unpack_concepts(id_term_cat_val_rxVar_wdOrder, rxVar=rxVar)
        
    def _unpack_concepts(self,id_term_cat_val_rxVar_wdOrder):
        '''
        Organizes input from database
        Parameters:
            id_term_cat_val_rxVar_wdOrder - list of (id, term, category, valence,
                                       regex_variation, word_order)
                * id - number
                * term - ctakes dictionary "text" field
                * category - like s21 for sumres21 (DCIS)
                * valence - 0 if term contains a negation/uncertainty term   
                * word_order- 0: free word order
                            1: enforce first word constraint
                            2: require precise word order
                * regex_variation-
                            0: no variation; words must be exact
                            1: minimal variation
                            2: moderate variation
                            3: flexible     
        '''
        self.wordlist = []
        for cid,term,cat,val,rxVar,wdOrder in id_term_cat_val_rxVar_wdOrder:
            self.cid_to_cat[cid] = cat
            self.cid_to_val[cid] = val
            self.cid_word_order[cid] = wdOrder
            if wdOrder == 0: # free word order
                self.cid_to_tids[cid] = set()
            elif wdOrder > 0: # restricted word order
                self.cid_to_tids[cid] = list()
                
            for word in term.split():
                self.wordlist.append( (word, self.wordID, rxVar) )
                if wdOrder == 0:
                    self.cid_to_tids[cid].add(self.wordID)
                if wdOrder > 0:
                    self.cid_to_tids[cid].append(self.wordID)
                self.wordID += 1
    
    def getWordlist(self,id_term_cat_val_rxVar_wdOrder=None):
        if id_term_cat_val_rxVar_wdOrder:
            self._unpack_concepts(id_term_cat_val_rxVar_wdOrder)
        return self.wordlist
        
    def addConversion(self, newTid_to_oldTids):
        '''
        Adds new one-to-many relations between 
        term_ids. Each term-id may only appear
        either on the RHS or the LHS of the dict
        (a.k.a., either keys or values, but not both)
        
        Parameters:
            newTid_to_oldTids -
                dictionary {newTid : set( [oldTid,oldTid,etc.])}
                where set(newTids) & set(oldTids) == set()
        '''
        
        if not self.tid_to_tid: # no extant conversions
            self.tid_to_tid = copy.deepcopy(newTid_to_oldTids)
        else:
            for newTid in newTid_to_oldTids:
                destinationTids = set()
                for oldTid in newTid_to_oldTids[newTid]:
                    destinationTids.add(newTid)
                    if oldTid in self.tid_to_tid:
                        destinationTids |= self.tid_to_tid[oldTid]
                        del self.tid_to_tid[oldTid]
                if newTid in self.tid_to_tid:
                    self.tid_to_tid[newTid] |= destinationTids
                else:
                    self.tid_to_tid[newTid] = destinationTids
        
    def getOriginalTermID(self, term_ids):
        if isinstance(term_ids, numbers.Real):
            term_ids = [term_ids]
            
        result = set(term_ids)
        for term_id in term_ids:
            if term_id in self.tid_to_tid:
                result |= self.tid_to_tid[term_id]
        return result
        
        
    def _checkValence(self,cid,judgment):
        """
        Checks the value of the term's valence. 
        If valence==0, then the term must be negated in order to be positive.
            -e.g., 'hyperplasia without atypia' since 'without' will make
                    the entire phrase negative
        If valence==1, then the term is treated normally
            -e.g., 'hyperplasia with atypia'
            
        Return:
            True - should be negated
            False - should not be negated
        """
        if self.cid_to_val[cid]: # is 1
            return judgment
        return not judgment
        
        
    def _getRemaining(self, allTermIds, currTermIds, wordOrder, firstWord=False):
        '''
        1. Check if there is an overlap between those terms desired by the current
        concept (allTermIds) and the currently found term (currTermIds)
            if not, return None
        2. Get the remaining terms for the current concept, and return them
        
        * word_order- 0: free word order
                    1: enforce first word constraint
                    2: require precise word order
        * firstWord- True: current term is first word of potential concept
                     False: current term is in middle/end of potential concept
        '''
        if wordOrder == 0 or (wordOrder == 1 and not firstWord):
            sharedSet = (allTermIds & currTermIds)
            if sharedSet:
                remainSet = (currTermIds - sharedSet)
                return remainSet
            else:
                return None
        elif wordOrder == 1 and firstWord:
            if currTermIds[0] in allTermIds:
                remainSet = set( currTermIds[1:] )
                return remainSet
            else:
                return None
        elif wordOrder == 2:
            if currTermIds[0] in allTermIds:
                remainList = currTermIds[1:]
                return remainList
            else:
                return None
            
        
    
        
    def aggregate(self,words, maxLengthOfSearch=2, maxNumberInterveningTerms=1):
        '''
        Aggregate terms into concepts according to the given
        mappings.
        
        Parameters:
            words-list of word-derived objects including
                negation, words, and terms
                only Terms will be considered in determining
                concepts
            maxLengthOfSearch- maximum number of words to look at; increments
            maxNumberInterveningTerms- maximum allowed number of intervening words
                between words in concept
            
        '''
        concepts = []
        words.sort()
        for i in xrange(len(words)):
            cword = words[i]
            if isinstance(cword,Term):        
                cAllTids = set( self.getOriginalTermID(cword.id()) )
                for cid in self.cid_to_tids: # look through concepts
                    remainSet = self._getRemaining(cAllTids, self.cid_to_tids[cid], self.cid_word_order[cid], firstWord=True)
                    
                    if remainSet is None: continue # return type of None was not a match
                    
                    # check if concept was completed
                    if remainSet:
                        concept = self._aggregate(words[i+1:], 
                                                    remainSet,
                                                    cword.isNegated(),
                                                    cword.isPossible(), #added 2013-11-05
                                                    cword.begin(),
                                                    cid,
                                                    maxLengthOfSearch, 
                                                    maxNumberInterveningTerms,
                                                    self.cid_word_order[cid]) #word order (added 2013-11-19)
                    else: # one-term concept (remainSet is empty list/set)
                        concept = Concept(cword.word(),
                                          cword.begin(),
                                          cword.end(),
                                          cid,
                                          self.cid_to_cat[cid],
                                          self._checkValence(cid,cword.isNegated()),
                                          cword.isPossible()) # added 2013-11-05

#                     print '    ',concepts
                    if concept: # function might return "False"
                        concepts.append( concept )
            else:
                continue
        return concepts
                
    def _aggregate(self, words, remainSet, negated, possible, startIdx, cid,
                    maxLengthOfSearch, maxNumberInterveningTerms, wordOrder):
        # see if matching terms are available in the next
        # couple terms
        wordsToFind = maxLengthOfSearch
        termsToFind = maxNumberInterveningTerms
        for j in xrange(len(words)):
#             print "    ",words[j], j, wordsToFind, termsToFind
            if j < wordsToFind and termsToFind >= 0:
                nword = words[j]
                if isinstance(nword, Term):
#                     print "  Next:",nword,wordsToFind,termsToFind
                    nAllTids = set( self.getOriginalTermID(nword.id()) )
                    tempRemainSet = self._getRemaining(nAllTids, remainSet, wordOrder, firstWord=False)

                    if tempRemainSet is None:
                        termsToFind -= 1
                    else:
                        wordsToFind += 2
                        if tempRemainSet: # more terms to find
                            negated = (negated or nword.isNegated())
                            possible = (possible or nword.isPossible()) # added 2013-11-05
                            remainSet = tempRemainSet
                        else: # empty list or set (not None)
                            return Concept('',
                                           startIdx,
                                           words[j].end(),
                                           cid, 
                                           self.cid_to_cat[cid],
                                           self._checkValence(cid,negated or nword.isNegated()),
                                           possible or nword.isPossible()) # added 2013-11-05

            else:
                break
        return False

    
class MinerCask(object):
    
    def __init__(self, id_term_cat_val_rxVar_wdOrder, negation_tuples, max_intervening_terms=2):
        '''
        
        Parameters
        ------------
        id_term_cat_val - list of (id, term, category, valence)
            id: unique id for each term
            term: space-separated words (phrase) to be found
            category: can be None; optional category
            valence: 1 (positive mention), 0 (negative mention)
        negation_tuples - negations as list of (negation_word, type)
            where type is 4 letter code from NegEx
        '''
        # prepare concept miner
        self.miner = ConceptMiner(id_term_cat_val_rxVar_wdOrder)
        self.rx_id, newTids_to_origTids = convert.convertToRegex(self.miner.getWordlist())
        self.miner.addConversion(newTids_to_origTids)
        self.table = string.maketrans("","")
        
        # prepare negation tagger
        self.tagger = myNegTagger(sortRulesFromTuple(negation_tuples))
        if max_intervening_terms:
            self.max_intervening_terms = max_intervening_terms
        else:
            self.max_intervening_terms = 2
        
    def mine(self, sentences, max_intervening_terms=None, max_length_of_search=3):
        if max_intervening_terms is None:
            max_intervening_terms = self.max_intervening_terms
        if isinstance(sentences,basestring):
            sentences = [sentences]
        resultConcepts = []
        offset = 0 # length of all previous sentences (for Concept location)
        for orig_sentence in sentences[:-1]:
            sentence = self.prepare(orig_sentence)
            #print sentence
            termList = clean_terms(find_terms(self.rx_id,sentence,offset=offset)) #added 20131212, meant to add to conceptminer2   
            termList += self.tagger.findNegation(sentence)
            termList += add_words(termList, sentence)
            termList.sort()
            sentence = self.tagger.negateSentence(termList)
            
            resultConcepts.append( self.miner.aggregate(sentence, maxLengthOfSearch=max_length_of_search,
                                                        maxNumberInterveningTerms=max_intervening_terms) )
            
            offset += len( orig_sentence )
            
        return resultConcepts
        
    def prepare(self, sentence):
        try:
            sentence = remove_punct(sentence)
        except Exception as e:
            print "Failed:",sentence
            print type(sentence)
            raise e
        return ' '.join( sentence.split() )
        
    
def assert_words(lst):
    types = {}
    for el in lst:
        t = type(el),
        if t in types:
            types[t] += 1
        else:
            types[t] = 1
    for t in types:
        print t,':',types[t]
    print '-' * 20

    
    
def mine(id_term_cat, negation_tuples, textList):
    """
    @ deprecated
    This function has been replaced by the class MinerCask
    which provides the MinerCask.mine function with 
    comparable functionality (and improved speed).
    """
    if isinstance(textList,str):
        textList = [textList]

    miner = ConceptMiner(id_term_cat)
    rx_id,newTids_to_origTids = convert.convertTextToRegex(miner.getWordlist())
    miner.addConversion(newTids_to_origTids)
    
    tagger = myNegTagger(sortRulesFromTuple(negation_tuples))
    
    result_texts = []
    for text in textList:
        text = ' '.join(text.split()) # condense whitespace
        
        termList = clean_terms(find_terms(rx_id,text))    
        
        termList += tagger.findNegation(text)
        termList += add_words(termList,text)
        termList.sort()
        sentence = tagger.negateSentence(termList)
        print 'before'
        result_texts.append( miner.aggregate(sentence) )
        
    return result_texts