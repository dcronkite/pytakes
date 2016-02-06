"""
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

"""
import copy
import numbers
from . import convert
from .negex import *


def remove_punct(text):
    return re.sub(r'\p{P}+', '', text)


class ConceptMiner(object):
    def __init__(self, id_term_cat_val_rxvar_wdorder, rx_var=0):
        self.cid_to_cat = {}  # ConceptID -> category
        self.cid_to_tids = {}  # ConceptID to TermIDs
        self.wordID = 0
        self.tid_to_tid = {}  # one-to-many new term ids to old term ids
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
            self.cid_to_cat[cid] = cat
            self.cid_to_val[cid] = val
            self.cid_word_order[cid] = wdOrder
            if wdOrder == 0:  # free word order
                self.cid_to_tids[cid] = set()
            elif wdOrder > 0:  # restricted word order
                self.cid_to_tids[cid] = list()

            for word in term.split():
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
                destinationtids = set()
                for oldTid in newtid_to_oldtids[newTid]:
                    destinationtids.add(newTid)
                    if oldTid in self.tid_to_tid:
                        destinationtids |= self.tid_to_tid[oldTid]
                        del self.tid_to_tid[oldTid]
                if newTid in self.tid_to_tid:
                    self.tid_to_tid[newTid] |= destinationtids
                else:
                    self.tid_to_tid[newTid] = destinationtids

    def get_original_term_id(self, term_ids):
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
        return not judgment

    def _get_remaining(self, all_term_ids, curr_term_ids, word_order, fword=False):
        """
        1. Check if there is an overlap between those terms desired by the current
        concept (all_term_ids) and the currently found term (curr_term_ids)
            if not, return None
        2. Get the remaining terms for the current concept, and return them

        * word_order- 0: free word order
                    1: enforce first word constraint
                    2: require precise word order
        * fword- True: current term is first word of potential concept
                     False: current term is in middle/end of potential concept
        """
        if word_order == 0 or (word_order == 1 and not fword):
            shared_set = (all_term_ids & curr_term_ids)
            if shared_set:
                remain_set = (curr_term_ids - shared_set)
                return remain_set
            else:
                return None
        elif word_order == 1 and fword:
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

    def aggregate(self, words, max_length_of_search=2, max_num_intervening_terms=1):
        """
        Aggregate terms into concepts according to the given
        mappings.

        Parameters:
            words-list of word-derived objects including
                negation, words, and terms
                only Terms will be considered in determining concepts
            max_length_of_search- maximum number of words to look at; increments
            max_num_intervening_terms- maximum allowed number of intervening words
                between words in concept

        """
        concepts = []
        words.sort()
        for i in range(len(words)):
            cword = words[i]
            if isinstance(cword, Term):
                c_all_tids = set(self.get_original_term_id(cword.id()))
                for cid in self.cid_to_tids:  # look through concepts
                    remain_set = self._get_remaining(c_all_tids, self.cid_to_tids[cid], self.cid_word_order[cid],
                                                     fword=True)

                    if remain_set is None: continue  # return type of None was not a match

                    # check if concept was completed
                    if remain_set:
                        concept = self._aggregate(words[i + 1:],
                                                  remain_set,
                                                  cword.is_negated(),
                                                  cword.is_possible(),  # added 2013-11-05
                                                  cword.begin(),
                                                  cid,
                                                  max_length_of_search,
                                                  max_num_intervening_terms,
                                                  self.cid_word_order[cid])  # word order (added 2013-11-19)
                    else:  # one-term concept (remain_set is empty list/set)
                        concept = Concept(cword.word(),
                                          cword.begin(),
                                          cword.end(),
                                          cid,
                                          self.cid_to_cat[cid],
                                          self._check_valence(cid, cword.is_negated()),
                                          cword.is_possible())  # added 2013-11-05

                    if concept:  # function might return "False"
                        concepts.append(concept)
            else:
                continue
        return concepts

    def _aggregate(self, words, remain_set, negated, possible, start_idx, cid,
                   max_length_of_search, max_num_intervening_terms, word_order):
        # see if matching terms are available in the next
        # couple terms
        words_to_find = max_length_of_search
        terms_to_find = max_num_intervening_terms
        for j in range(len(words)):
            #             print "    ",words[j], j, words_to_find, terms_to_find
            if j < words_to_find and terms_to_find >= 0:
                nword = words[j]
                if isinstance(nword, Term):
                    #                     print "  Next:",nword,words_to_find,terms_to_find
                    n_all_tids = set(self.get_original_term_id(nword.id()))
                    temp_remain_set = self._get_remaining(n_all_tids, remain_set, word_order, fword=False)

                    if temp_remain_set is None:
                        terms_to_find -= 1
                    else:
                        words_to_find += 2
                        if temp_remain_set:  # more terms to find
                            negated = (negated or nword.is_negated())
                            possible = (possible or nword.is_possible())  # added 2013-11-05
                            remain_set = temp_remain_set
                        else:  # empty list or set (not None)
                            return Concept('',
                                           start_idx,
                                           words[j].end(),
                                           cid,
                                           self.cid_to_cat[cid],
                                           self._check_valence(cid, negated or nword.is_negated()),
                                           possible or nword.is_possible())  # added 2013-11-05

            else:
                break
        return False


# noinspection PyUnresolvedReferences
class MinerCask(object):
    def __init__(self, id_term_cat_val_rxvar_wdorder, negation_tuples, max_intervening_terms=2):
        """

        Parameters
        ------------
        id_term_cat_val - list of (id, term, category, valence)
            id: unique id for each term
            term: space-separated words (phrase) to be found
            category: can be None; optional category
            valence: 1 (positive mention), 0 (negative mention)
        negation_tuples - negations as list of (negation_word, type)
            where type is 4 letter code from NegEx
        """
        # prepare concept miner
        self.miner = ConceptMiner(id_term_cat_val_rxvar_wdorder)
        self.rx_id, new_tids_to_orig_tids = convert.convert_to_regex(self.miner.get_wordlist())
        self.miner.add_conversion(new_tids_to_orig_tids)
        self.table = str.maketrans("", "")

        # prepare negation tagger
        self.tagger = MyNegTagger(sort_rules_from_tuple(negation_tuples))
        if max_intervening_terms:
            self.max_intervening_terms = max_intervening_terms
        else:
            self.max_intervening_terms = 2

    def mine(self, sentences, max_intervening_terms=None, max_length_of_search=3):
        if max_intervening_terms is None:
            max_intervening_terms = self.max_intervening_terms
        if isinstance(sentences, str):
            sentences = [sentences]
        result_concepts = []
        offset = 0  # length of all previous sentences (for Concept location)
        for orig_sentence in sentences[:-1]:
            sentence = self.prepare(orig_sentence)
            # print sentence
            termlist = clean_terms(
                find_terms(self.rx_id, sentence, offset=offset))  # added 20131212, meant to add to conceptminer2
            termlist += self.tagger.find_negation(sentence)
            termlist += add_words(termlist, sentence)
            termlist.sort()
            sentence = self.tagger.negate_sentence(termlist)

            result_concepts.append(self.miner.aggregate(sentence, max_length_of_search=max_length_of_search,
                                                        max_num_intervening_terms=max_intervening_terms))

            offset += len(orig_sentence)

        return result_concepts

    def prepare(self, sentence):
        try:
            sentence = remove_punct(sentence)
        except Exception as e:
            print("Failed:", sentence)
            print(type(sentence))
            raise e
        return ' '.join(sentence.split())


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


def mine(id_term_cat, negation_tuples, textlist):
    """
    @ deprecated
    This function has been replaced by the class MinerCask
    which provides the MinerCask.mine function with 
    comparable functionality (and improved speed).
    """
    if isinstance(textlist, str):
        textlist = [textlist]

    miner = ConceptMiner(id_term_cat)
    rx_id, newtids_to_origtids = convert.convert_text_to_regex(miner.get_wordlist())
    miner.add_conversion(newtids_to_origtids)

    tagger = MyNegTagger(sort_rules_from_tuple(negation_tuples))

    result_texts = []
    for text in textlist:
        text = ' '.join(text.split())  # condense whitespace

        termlist = clean_terms(find_terms(rx_id, text))

        termlist += tagger.find_negation(text)
        termlist += add_words(termlist, text)
        termlist.sort()
        sentence = tagger.negate_sentence(termlist)
        result_texts.append(miner.aggregate(sentence))

    return result_texts
