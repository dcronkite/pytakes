import csv
import platform
from pathlib import Path

from .base import Dictionary, Output, Document
from ..dict.textitem import TextItem
from ..nlp.terms import Concept


class CsvDictionary(Dictionary):

    def __init__(self, name=None, path=None, valence=1, regex_variation=0, word_order=1,
                 max_intervening=1, max_search=2, **kwargs):
        super().__init__(name=name, **kwargs)
        self.valence = valence
        self.regex_variation = regex_variation
        self.word_order = word_order
        self.max_intervening = max_intervening
        self.max_search = max_search
        if name and path:
            self.fp = path / self.name
        elif name:
            self.fp = Path(self.name)
        else:
            self.fp = path
            self.name = path.stem

    def read(self):
        return self._get_terms()

    def _get_terms(self):
        """
        Retrieve terms from table.
        Function checks to see if optional columns are present,
        otherwise uses cTAKES defaults.
        """
        columns = {}
        res = []
        with open(self.fp) as fh:
            for i, line in enumerate(csv.reader(fh)):
                if i == 0:
                    columns = {x.lower(): i for i, x in enumerate(line)}
                else:
                    res.append((
                        line[columns['id']],
                        line[columns['text']],
                        line[columns['cui']],
                        self.int_or_default(line[columns.get('valence', self.valence)], self.valence),
                        self.int_or_default(line[columns.get('regexvariation', self.regex_variation)],
                                            self.regex_variation),
                        self.int_or_default(line[columns.get('wordorder', self.word_order)], self.word_order),
                        self.int_or_default(line[columns.get('maxintervening', self.max_intervening)],
                                            self.max_intervening),
                        self.int_or_default(line[columns.get('maxwords', self.max_search)], self.max_search),
                    ))
        return res


class CsvDocument(Document):

    def get_ids(self):
        pass

    def __len__(self):
        pass

    def __init__(self, path=None, order_by=None, batch_size=None, meta=None,
                 text=None, **config):
        super().__init__(**config)
        self.text = text
        self.meta = meta
        self.order_by = order_by
        self.batch_size = batch_size
        self.fp = path / self.name

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

    def __init__(self, name=None, path=None, metalabels=None,
                 types=None, hostname=None, batch_number=None, **config):
        super().__init__(name=name, **config)
        self.labels = (metalabels or []) + self.all_labels
        self.types = types
        self.hostname = hostname or platform.node()
        self.batch_number = batch_number
        self.fh = open(path / self.name, 'w', newline='')
        self.writer = csv.writer(self.fh)
        self.writer.writerow(self.labels)  # header

    def writerow(self, feat: Concept, meta=None, text=None):
        if not meta:
            meta = []
        if text:
            length = len(text)
            self.writer.writerow(meta +
                                 [feat.id(),
                                  feat.cat(),
                                  self._get_text(text, feat.begin(), feat.end()),
                                  self._get_text(text, self._get_index(length, feat.begin() - self.context_width),
                                                 self._get_index(length, feat.end() + self.context_width)),
                                  feat.get_certainty(),
                                  feat.is_hypothetical(),
                                  feat.is_historical(),
                                  feat.is_not_patient(),
                                  feat.get_absolute_begin(),
                                  feat.get_absolute_end(),
                                  self.hostname,
                                  self.batch_number
                                  ]
                                 )
        else:  # no text
            self.writer.writerow(meta +
                                 [text[feat.begin():feat.end()].strip(),
                                  None,
                                  None,
                                  None,
                                  None,
                                  None,
                                  self.hostname,
                                  self.batch_number
                                  ]
                                 )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fh.close()
