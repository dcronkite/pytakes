import regex as re
from utils import replace_punctuation, is_number

_1GRAM = '1gram'
_2GRAM = '2gram'
_3GRAM = '3gram'
_4GRAM = '4gram'
_S2GRAM = 's2gram'
_S3GRAM = 's3gram'
NUMBER = '<NUMBER>'
JOINER = '_'


class Feature(object):

    ID_COUNTER = 0

    def __init__(self, feature, category):
        self.id = self._get_id()
        self.feature = feature
        self.category = category

    def _get_id(self):
        self.ID_COUNTER += 1
        return self.ID_COUNTER

    def feature(self):
        return self.feature

    def category(self):
        return self.category

    def id(self):
        return self.id


class Excluder:
    def __init__(self, stopwords=None, patterns=None):
        """
        Create an instance used to exclude features from consideration.
        :param stopwords: skip these words when collecting features
        :param patterns: do not include any features with this pattern
        :return:
        """
        self.stopwords = set(stopwords)
        self.patterns = [re.compile(p) for p in patterns]
        if self.stopwords or self.patterns:
            self.excluding = True
        else:
            self.excluding = False

    def __contains__(self, item):
        return item in self.stopwords

    def exclude(self, feature, joiner):
        if self.patterns:
            for pat in self.patterns:
                for feat in feature.split(joiner) + [feature]:
                    if pat.match(feat):
                        return False
        return True


class FeatureMiner(object):

    def __init__(self, stopwords=None, patterns=None, number_norm=True):
        self.excluder = Excluder(stopwords, patterns)
        self.number_norm = number_norm

    def _add_feature(self, features, ngram, category, joiner=JOINER):
        if not self.excluder.exclude(ngram, joiner):
            features.append(Feature(ngram, category))

    def mine(self, sentences):
        """
        computes all types of ngrams in one pass

        features: dict of feature -> count
        sentences: list of sentences: list of strings
        number_norm: whether to normalize numbers or not
        excluder: instance of feature.Excluder
        """
        features = []
        for phrase in sentences:
            pppw = None
            ppw = None
            pw = None
            us = JOINER
            for word in phrase:
                word = word.lower()
                if self.excluder.excluding and word in self.excluder:
                    continue  # ignore word
                elif self.number_norm and is_number(word):
                    word = NUMBER
                else:
                    word = replace_punctuation(word)
                self._add_feature(features, word, _1GRAM)  # unigram
                if pw:
                    self._add_feature(features, us.join((pw, word)), _2GRAM)  # bigram
                    if ppw:
                        self._add_feature(features, us.join((ppw, pw, word)), _3GRAM)  # trigram
                        self._add_feature(features, us.join((ppw, word)), _S2GRAM)  # split bigram
                        if pppw:
                            self._add_feature(features, us.join((pppw, word)), _S2GRAM)  # split bigram
                            self._add_feature(features, us.join((pppw, ppw, word)), _S3GRAM)  # split trigram
                            self._add_feature(features, us.join((pppw, pw, word)), _S3GRAM)  # split trigram
                            self._add_feature(features, us.join((pppw, ppw, pw, word)), _4GRAM)  # 4gram
                # assignments for next pass
                pppw = ppw
                ppw = pw
                pw = word
        return features
