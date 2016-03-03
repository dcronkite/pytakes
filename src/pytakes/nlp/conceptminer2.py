"""
ghri.wildcat.conceptminer2.py
    created: 2013-04-18

Purpose:
    Mine concepts from the text. Essentially do what cTAKES does,
    but do it better AND simpler.

Author:
    Cronkite, David (GHRI)

Edits:
2013-11-05    added possible tags
2013-11-26    replaced by conceptminer2 for additional assertion annotation
-- conceptminer2 --
2013-12-12    added

"""
import copy
import numbers

import regex as re

from pytakes.nlp import convert
from pytakes.nlp.terms import Term, Concept, clean_terms, add_words, find_terms
from .negex import MyStatusTagger, sort_rules_for_status


def remove_punct(text):
    return re.sub(r'\p{P}', ' ', text)


class ConceptMiner(object):
    def __init__(self, id_term_cat_val_rxvar_wdorder):
        self.cid_to_cat = {}  # ConceptID -> category
        self.cid_to_tids = {}  # ConceptID to TermIDs
        self.wordID = 0
        self.tid_to_tid = {}  # list of conversions of
        # new TermIDs to old TermIDs
        # this should be a one-to-many
        # relationship where one New
        # TermID is equivalent to several
        # older TermIDs
        # no reason to have it the other
        # way around
        self.cid_to_val = {}
        self.cid_word_order = {}  # word order constraints
        self.wordlist = []

        self._unpack_concepts(id_term_cat_val_rxvar_wdorder)

    def _unpack_concepts(self, id_term_cat_val_rxvar_wdorder):
        """
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
        """
        self.wordlist = []
        for cid, term, cat, val, rxVar, wdOrder in id_term_cat_val_rxvar_wdorder:
            # update references of ConceptID (think "CUI")
            self.cid_to_cat[cid] = cat
            self.cid_to_val[cid] = val
            self.cid_word_order[cid] = wdOrder
            if wdOrder == 0:  # free word order
                self.cid_to_tids[cid] = set()
            elif wdOrder > 0:  # restricted word order
                self.cid_to_tids[cid] = list()

            for word in term.split():
                # give each word a unique id, and treated uniquely
                self.wordlist.append((word, self.wordID, rxVar))
                if wdOrder == 0:
                    self.cid_to_tids[cid].add(self.wordID)
                if wdOrder > 0:
                    self.cid_to_tids[cid].append(self.wordID)
                self.wordID += 1

    def get_wordlist(self, id_term_cat_val_rxvar_wdorder=None):
        if id_term_cat_val_rxvar_wdorder:
            self._unpack_concepts(id_term_cat_val_rxvar_wdorder)
        return self.wordlist

    def add_conversion(self, newtid_to_oldtids):
        """
        Adds new one-to-many relations between
        term_ids. Each term-id may only appear
        either on the RHS or the LHS of the dict
        (a.k.a., either keys or values, but not both)

        Parameters:
            newTid_to_oldTids -
                dictionary {newTid : set( [oldTid,oldTid,etc.])}
                where set(newTids) & set(oldTids) == set()
        """

        if not self.tid_to_tid:  # no extant conversions
            self.tid_to_tid = copy.deepcopy(newtid_to_oldtids)
        else:
            for newTid in newtid_to_oldtids:
                dest_tids = set()
                for oldTid in newtid_to_oldtids[newTid]:
                    dest_tids.add(newTid)
                    if oldTid in self.tid_to_tid:
                        dest_tids |= self.tid_to_tid[oldTid]
                        del self.tid_to_tid[oldTid]
                if newTid in self.tid_to_tid:
                    self.tid_to_tid[newTid] |= dest_tids
                else:
                    self.tid_to_tid[newTid] = dest_tids

    def get_original_term_id(self, term_ids):
        """
        Use the one-to-many mapping to get all possible term_ids for a particular term id (or list)

        @param term_ids: integer, or list of integers
        @return: all relevant term ids
        """
        if isinstance(term_ids, numbers.Real):
            term_ids = [term_ids]

        result = set(term_ids)
        for term_id in term_ids:
            if term_id in self.tid_to_tid:
                result |= self.tid_to_tid[term_id]
        return result

    def _check_valence(self, cid, judgment):
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
        if self.cid_to_val[cid]:  # is 1
            return judgment
        return 4 - judgment  # get inverse of certainty

    def _get_remaining(self, all_term_ids, curr_term_ids, word_order, first_word=False):
        """
        1. Check if there is an overlap between those terms desired by the current
            concept (all_term_ids) and the currently found term (curr_term_ids)
            if not, return None
        2. Get the remaining terms for the current concept, and return them

        @param all_term_ids:
        @param curr_term_ids:
        @param word_order: 0: free word order
                    1: enforce first word constraint
                    2: require precise word order
        @param first_word: True: current term is first word of potential concept
                     False: current term is in middle/end of potential concept
        @return: remaining terms for the current concept (empty list of all found), or None not found
        """
        if word_order == 0 or (word_order == 1 and not first_word):
            shared_set = (all_term_ids & curr_term_ids)
            if shared_set:
                remain_set = (curr_term_ids - shared_set)
                return remain_set
            else:
                return None
        elif word_order == 1 and first_word:
            if curr_term_ids[0] in all_term_ids:
                remain_set = set(curr_term_ids[1:])
                return remain_set
            else:
                return None
        elif word_order == 2:
            if curr_term_ids[0] in all_term_ids:
                remain_list = curr_term_ids[1:]
                return remain_list
            else:
                return None

    def aggregate(self, words, max_length_of_search=2, max_intervening_terms=1):
        """
        Aggregate terms (in the word list) into concepts according.

        @param words: list of word-derived objects including negation, words, and terms
            only Terms will be considered in determining concepts
        @param max_length_of_search: maximum number of words to look at; increments
        @param max_intervening_terms: maximum allowed number of intervening words
            between words in concept
        @return: all found concepts

        """
        concepts = []
        words.sort()
        for i in range(len(words)):
            cword = words[i]
            if isinstance(cword, Term):
                c_all_tids = set(self.get_original_term_id(cword.id()))
                for cid in self.cid_to_tids:  # look through concepts
                    remain_set = self._get_remaining(c_all_tids, self.cid_to_tids[cid], self.cid_word_order[cid],
                                                     first_word=True)

                    if remain_set is None: continue  # return type of None was not a match

                    # check if concept was completed
                    if remain_set:  # concept has additional terms (> 1 word)
                        concept = self._aggregate(words[i:],
                                                  remain_set,
                                                  cword.get_certainty(),
                                                  cword.is_hypothetical(),
                                                  cword.is_historical(),
                                                  cword.is_not_patient(),
                                                  cword.begin(),
                                                  cid,
                                                  max_length_of_search,
                                                  max_intervening_terms,
                                                  self.cid_word_order[cid])  # word order (added 2013-11-19)
                    else:  # one-term concept (remain_set is empty list/set)
                        concept = Concept(cword.word(),
                                          cword.begin(),
                                          cword.end(),
                                          cid,
                                          self.cid_to_cat[cid],
                                          self._check_valence(cid, cword.get_certainty()),
                                          cword.is_hypothetical(),
                                          cword.is_historical(),
                                          cword.is_not_patient())
                    if concept:  # function might return "False"
                        concepts.append(concept)
            else:  # current word is not a Term
                continue
        return concepts

    def _aggregate(self, words, remain_set, certainty, hypothetical, historical,
                   not_patient, start_idx, cid, words_to_look_at, max_intervening_words, word_order):
        """
        Look through subsequent words for additional terms to determine if the concept is contained in the text.

        @param words: list of words and Terms (which compose concepts)
        @param remain_set: remaining words to complete concept
        @param certainty: negex status of first found term in concept
        @param hypothetical: negex status of first found term in concept
        @param historical: negex status of first found term in concept
        @param not_patient: negex status of first found term in concept
        @param start_idx: starting index of first word in concept
        @param cid: concept id of concept
        @param words_to_look_at: maximum number of words to look at
        @param max_intervening_words: maximum allowed number of intervening words between words in concept
        @param word_order: word ordering requirements for current concept
        @return: found Concept or False
        """
        words_to_look_at_incr = words_to_look_at
        orig_words = words
        words = words[1:]
        # see if matching terms are available in the next couple terms
        for j in range(len(words)):
            if j < words_to_look_at and max_intervening_words >= 0:
                nword = words[j]
                if isinstance(nword, Term):
                    # check if current term is present in current concept
                    n_all_tids = set(self.get_original_term_id(nword.id()))
                    temp_remain_set = self._get_remaining(n_all_tids, remain_set, word_order, first_word=False)

                    if temp_remain_set is None:  # term not in concept
                        max_intervening_words -= 1
                    else:  # term in concept
                        words_to_look_at += words_to_look_at_incr
                        # update negex status with more egregious form
                        certainty = min(certainty, nword.get_certainty())
                        hypothetical = max(hypothetical, nword.is_hypothetical())
                        historical = max(historical, nword.is_historical())
                        not_patient = max(not_patient, nword.is_not_patient())
                        if temp_remain_set:  # more terms to find
                            remain_set = temp_remain_set
                        else:  # empty list or set (cannot be None)
                            return Concept(' '.join([w.word() for w in orig_words[:j + 2]]),
                                           start_idx,
                                           words[j].end(),
                                           cid,
                                           self.cid_to_cat[cid],
                                           self._check_valence(cid, certainty),
                                           hypothetical,
                                           historical,
                                           not_patient)

            else:
                break
        return False


class MinerCask(object):
    def __init__(self, id_term_cat_val_rxvar_wdorder, negation_tuples, rxvar=0, max_intervening_terms=2):
        """

        Parameters
        ------------
        id_term_cat_val_rxVar_wdOrder - list of (id, term, category, valence, rxVar, wdOrder)
        :rtype : MinerCask
            id: unique id for each term
            term: space-separated words (phrase) to be found
            category: can be None; optional category
            valence: 1 (positive mention), 0 (negative mention)
        negation_tuples - negations as list of (negation_word, type)
            where type is 4 letter code from NegEx
        """
        # prepare concept miner
        self.miner = ConceptMiner(id_term_cat_val_rxvar_wdorder)
        self.rx_id, newTids_to_origTids = convert.convert_to_regex(self.miner.get_wordlist())
        self.miner.add_conversion(newTids_to_origTids)
        self.table = str.maketrans("", "")

        # prepare negation tagger
        self.tagger = MyStatusTagger(sort_rules_for_status(negation_tuples))
        if max_intervening_terms:
            self.max_intervening_terms = max_intervening_terms
        else:
            self.max_intervening_terms = 2

    def mine(self, sentences, max_length_of_search=3, max_intervening_terms=None):
        if max_intervening_terms is None:
            max_intervening_terms = self.max_intervening_terms
        if isinstance(sentences, str):
            sentences = [sentences]
        resultconcepts = []
        offset = 0  # length of all previous sentences (for Concept location)
        for orig_sentence in sentences:
            sentence = self.prepare(orig_sentence)
            termlist = clean_terms(find_terms(self.rx_id, sentence, offset=offset))
            termlist += self.tagger.find_negation(sentence)
            termlist += add_words(termlist, sentence)
            termlist.sort()
            sentence = self.tagger.analyze_sentence(termlist)
            resultconcepts.append(self.miner.aggregate(sentence, max_length_of_search=max_length_of_search,
                                                       max_intervening_terms=max_intervening_terms))
            # change orig_sentence to sentence to get an offset
            # that is true after the "prepare" statement below
            offset += len(orig_sentence)
        return resultconcepts

    def prepare(self, sentence):
        return sentence


def assert_words(lst):
    types = {}
    for el in lst:
        t = type(el),
        if t in types:
            types[t] += 1
        else:
            types[t] = 1
    for t in types:
        print(t, ':', types[t])
    print('-' * 20)
