from pytakes.nlp.miner import Miner
from pytakes.nlp.terms import add_words


class MinerCollection(object):

    def __init__(self, ssplit=None, cleaner=None, add_intervening_words=True):
        self.miners = []
        self.ssplit = ssplit
        self.cleaner = cleaner
        self.add_words = add_intervening_words

    def add(self, miner: Miner):
        self.miners.append(miner)

    def ssplit(self, text):
        if self.ssplit:
            for sentence in self.ssplit(' '.join(text.split('\n'))):
                yield sentence
        else:
            yield text

    def clean_sentence(self, sentence):
        if self.clean_sentence and self.cleaner:
            return self.cleaner(sentence)
        else:
            return sentence

    def parse_sentence(self, sentence, offset):
        terms = []
        for miner in self.miners:
            terms += miner.clean(miner.mine(sentence, offset=offset))
        if self.add_words:
            terms += add_words(terms, sentence, offset=offset)
        terms.sort()
        for miner in self.miners:
            terms = miner.postprocess(terms)
        terms.sort()
        res = []
        for miner in self.miners:
            res += miner.extract(terms)
        offset += len(sentence)
        return res, sentence

    def parse(self, doc):
        offset = 0
        for sentence in self.ssplit(doc.get_text()):
            sent = self.clean_sentence(sentence)
            yield self.parse_sentence(sent, offset)
            offset += len(sent)