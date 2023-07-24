from ..nlp.collections import MinerCollection


class TextItem(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, text, **meta):
        self.meta = meta
        if isinstance(text, str):
            self.orig_text = [text]
        else:
            self.orig_text = [t.strip() for t in text if t.strip()]
        self.text = '\n'.join(self.fix(t) for t in self.orig_text)

    def fix(self, text):
        text = ' '.join(text.split('\n'))
        text.replace('don?t', "don't")  # otherwise the '?' will start a new sentence
        return text


def process_textitem(ti: TextItem, mc: MinerCollection):
    for res, sent in mc.parse(ti):
        yield res, sent


def process_text(text: str, mc: MinerCollection, **textmeta):
    """Create a TextItem and process the text."""
    for res, sent in mc.parse(TextItem(text, **textmeta)):
        yield res, sent
