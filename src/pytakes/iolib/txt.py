from pytakes import Dictionary


class TxtDictionary(Dictionary):

    def __init__(self, *rules, name=None, valence=1, regex_variation=0, word_order=1,
                 max_intervening=1, max_search=2, **kwargs):
        """
        Rules: tuples(id, text, cui)
        """
        super().__init__(name=name, **kwargs)
        self.rules = rules
        # other
        self.valence = valence
        self.regex_variation = regex_variation
        self.word_order = word_order
        self.max_intervening = max_intervening
        self.max_search = max_search

    def read(self):
        res = []
        tail = [self.valence, self.regex_variation, self.word_order, self.max_intervening, self.max_search]
        for i, rule in enumerate(self.rules):
            if isinstance(rule, str) or len(rule) == 1:  # just the text
                res.append(tuple([i, rule, f'C{i:07d}'] + tail))
            elif len(rule) == 2:  # assume is text, cui
                res.append(tuple([i, rule[0], rule[1]] + tail))
            else:  # just the text
                res.append(tuple([rule[0], rule[1], rule[2]] + tail))
        return res
