import logging
from pathlib import Path

try:
    from sas7bdat import SAS7BDAT
except ImportError:
    logging.warning(f'Missing SAS7BDAT library: will not be able to read from SAS.')
    SAS7BDAT = None

from .base import Dictionary, Document
from ..dict.textitem import TextItem


class SasDictionary(Dictionary):

    def __init__(self, path: Path = None, valence=None,
                 regex_variation=None, word_order=None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.valence = valence
        self.regex_variation = regex_variation
        self.word_order = word_order
        self.fp = path / self.name

    def read(self):
        logging.info('Getting Terms and Negation.')
        res = []
        with SAS7BDAT(self.fp) as fh:
            columns = fh.column_names_strings
            for row in fh:
                res.append([
                    row[columns['id']],
                    row[columns['text']],
                    row[columns['cui']],
                    row[columns['valence']],
                    row[columns['regexvariation']],
                    row[columns['wordorder']],
                ])
        return res


class SasDocument(Document):

    def __init__(self, path: Path = None, order_by=None, batch_size=None, meta=None,
                 text=None, **config):
        super().__init__(**config)
        self.text = text
        self.meta = meta
        self.order_by = order_by
        self.batch_size = batch_size
        self.fp = path / self.name

    def read_next(self):
        with SAS7BDAT(self.fp) as fh:
            for i, line in enumerate(fh):
                columns = {x: i for i, x in enumerate(line)}
                yield TextItem(
                    meta_list=[line[columns[m]] for m in self.meta],
                    text=[line[columns[t]] for t in self.text]
                )
