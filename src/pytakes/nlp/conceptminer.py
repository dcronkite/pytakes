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
from typing import List

from ..iolib.base import Dictionary
from . import convert
from .miner import Miner
from .terms import Term, Concept


class ConceptMiner(Miner):

    def __init__(self, dictionaries: List[Dictionary]):
        super().__init__()
        self.entries = [entry for d in dictionaries for entry in d.read()]
        self.cid_to_cat = {}  # ConceptID -> category
        self.cid_to_tids = {}  # ConceptID to TermIDs
        self.cid_search_param = {}
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

        self._unpack_concepts()

    def _unpack_concepts(self):
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
        for cid, term, cat, val, rxVar, wdOrder, max_intervening, max_search in self.entries:
            # update references of ConceptID (think "CUI")
            self.cid_to_cat[cid] = cat
            self.cid_to_val[cid] = val
            self.cid_word_order[cid] = wdOrder
            self.cid_search_param[cid] = (max_intervening, max_search)
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

        self.wordlist, upd_ids = convert.convert_to_regex(self.wordlist)

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

    def extract(self, terms):
        """
        Aggregate terms (in the word list) into concepts according.

        @param terms: list of word-derived objects including negation, words, and terms
            only Terms will be considered in determining concepts; must be sorted
        @return: all found concepts

        """
        concepts = []
        for i in range(len(terms)):
            cword = terms[i]
            if isinstance(cword, Term):
                c_all_tids = set(self.get_original_term_id(cword.id()))
                for cid in self.cid_to_tids:  # look through concepts
                    max_intervening, max_search = self.cid_search_param[cid]
                    remain_set = self._get_remaining(c_all_tids, self.cid_to_tids[cid], self.cid_word_order[cid],
                                                     first_word=True)

                    if remain_set is None:
                        continue  # return type of None was not a match

                    # check if concept was completed
                    if remain_set:  # concept has additional terms (> 1 word)
                        concept = self._aggregate(terms[i:],
                                                  remain_set,
                                                  cword.get_certainty(),
                                                  cword.is_hypothetical(),
                                                  cword.is_historical(),
                                                  cword.is_not_patient(),
                                                  cword.begin(),
                                                  cid,
                                                  max_search,
                                                  max_intervening,
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
                                          cword.is_not_patient(),
                                          offset=cword.offset_)
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
                                           not_patient,
                                           offset=nword.offset_)

            else:
                break
        return False

    def postprocess(self, terms):
        return terms  # no postprocessing

    def mine(self, text, offset):
        """
        Paramters:
            terms - list of (term,id) where unique id for each term
            :param text:
            :param offset:
        """
        results = []
        for term, id_ in self.wordlist:
            for m in term.finditer(text):
                results.append(Term(term, m.start(), m.end(), 'term', id_, offset=offset))
        return sorted(results)

    def clean(self, terms):
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
