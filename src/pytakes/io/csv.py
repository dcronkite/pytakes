import logging
import os
import csv

from pytakes.io.base import Dictionary, Output, Document
from pytakes.processor import TextItem


class CsvDictionary(Dictionary):

    def __init__(self, path=None, valence=None,
                 regex_variation=None, word_order=None, **kwargs):
        super().__init__(**kwargs)
        self.valence = valence
        self.regex_variation = regex_variation
        self.word_order = word_order
        self.fp = os.path.join(path, self.name)

    def read(self):
        return self._get_terms()

    def _get_terms(self):
        """
        Retrieve terms from table.
        Function checks to see if optional columns are present,
        otherwise uses cTAKES defaults.
        :param dbi:
        :param term_table:
        :param valence:
        :param regex_variation:
        :param word_order:
        """
        logging.info('Getting Terms and Negation.')
        columns = {}
        res = []
        with open(self.fp) as fh:
            for i, line in enumerate(csv.reader(fh)):
                if i == 0:
                    columns = {x: i for i, x in enumerate(line)}
                else:
                    res.append([
                        line[columns['id']],
                        line[columns['text']],
                        line[columns['cui']],
                        line[columns['valence']],
                        line[columns['regexvariation']],
                        line[columns['WordOrder']],
                    ])
        return res


class CsvDocument(Document):

    def __init__(self, path=None, order_by=None, batch_size=None, meta=None,
                 text=None, **config):
        super().__init__(**config)
        self.text = text
        self.meta = meta
        self.order_by = order_by
        self.batch_size = batch_size
        self.fp = os.path.join(path, self.name)

    def read_next(self):
        """
        Retrieve documents from table
        """
        columns = {}
        with open(self.fp) as fh:
            for i, line in enumerate(csv.reader(fh)):
                if i == 0:
                    columns = {x: i for i, x in enumerate(line)}
                else:
                    yield TextItem(
                        meta_list=[line[columns[m]] for m in self.meta],
                        text=[line[columns[t]] for t in self.text]
                    )


class CsvOutput(Output):

    def __init__(self, labels=None, path=None,
                 types=None, hostname=None, batch_number=None, **config):
        super().__init__(**config)
        self.labels = labels
        self.types = types
        self.hostname = hostname
        self.batch_number = batch_number
        self.fp = os.path.join(path, self.name)
        self.fh = None

    def create_output(self):
        self.fh = csv.writer(open(self.fp, 'w'))
        self.fh.writerow(self.labels)  # header

    def writerow(self, meta, feat, text=None):
        if text:
            length = len(text)
            self.fh.writerow(meta +
                             [text[feat.begin():feat.end()].strip(),
                              text[self._get_index(length, feat.begin() - 75):self._get_index(length, feat.end() + 75)],
                              feat.get_certainty(),
                              feat.is_hypothetical(),
                              feat.is_historical(),
                              feat.is_not_patient(),
                              self.hostname,
                              self.batch_number
                              ]
                             )
        else:
            self.fh.writerow(meta +
                             [text[feat.begin():feat.end()].strip(),
                              self.hostname,
                              self.batch_number
                              ]
                             )

    def close(self):
        if self.fh:
            self.fh.close()
