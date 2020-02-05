from ..nlp.collections import MinerCollection


class TextItem(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, text, **meta):
        self.meta = meta
        if isinstance(text, str):
            self._orig_text = [text]
        else:
            self._orig_text = [t for t in text if t]
        try:
            self.text_ = self.fix_text(text[0])
        except IndexError as e:
            self.text_ = ''
        for txt in text[1:]:
            self.add_text(txt)  # split added 20131224

    def get_orig_text(self):
        return self._orig_text[0]

    def add_text(self, text):
        self.text_ += '\n' + self.fix_text(text)

    def get_text(self):
        return self.text_

    def get_metalist(self):
        return self.meta

    def fix_text(self, text):
        text = ' '.join(text.split('\n'))
        text.replace('don?t', "don't")  # otherwise the '?' will start a new sentence
        return text


def process_textitem(ti: TextItem, mc: MinerCollection):
    for res, sent in mc.parse(ti):
        yield res, sent
