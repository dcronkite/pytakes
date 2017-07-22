"""
Base classes for interface.
"""
import abc

from pytakes.io.csv import CsvDictionary, CsvDocument, CsvOutput
from pytakes.io.sas import SasDictionary, SasDocument
from pytakes.io.sql import SqlDictionary, SqlDocument, SqlOutput

data_items = {
    'sql': {
        'dictionary': SqlDictionary,
        'document': SqlDocument,
        'output': SqlOutput
    },
    'sas': {
        'dictionary': SasDictionary,
        'document': SasDocument,
        # 'output': SasOutput  # not supported
    },
    'csv': {
        'dictionary': CsvDictionary,
        'document': CsvDocument,
        'output': CsvOutput
    }
}


def get_data_item(res, datatype, conn):
    try:
        return data_items[res['type']][datatype](**res, dbi=conn)
    except Exception as e:
        raise ValueError('Unsupported {} type: "{}"'.format(res['type'], datatype))


class Dictionary(metaclass=abc.ABCMeta):
    def __init__(self, name=None, **kwargs):
        self.name = name

    @abc.abstractmethod
    def read(self):
        pass


class Document(metaclass=abc.ABCMeta):
    def __init__(self, name=None, **config):
        self.name = name

    @abc.abstractmethod
    def __len__(self):
        pass

    @abc.abstractmethod
    def get_ids(self):
        pass

    @abc.abstractmethod
    def read_next(self):
        pass


class Output(metaclass=abc.ABCMeta):
    # columns
    all_labels = ['dictid', 'captured', 'context', 'text', 'certainty', 'hypothetical', 'historical',
                  'otherSubject', '"start"', '"finish"', 'start_idx', 'end_idx', 'cpu_name', 'version']
    all_types = ['int', 'varchar(255)', 'varchar(255)', 'varchar(max)', 'int',
                 'int', 'int', 'int', 'int', 'int', 'int', 'int', 'varchar(50)', 'int']
    all_labels = ['featid', 'feature', 'category', 'cpu_name', 'version']
    all_types = ['bigint', 'varchar(max)', 'varchar(50)', 'varchar(50)', 'int']

    def __init__(self, name=None, **config):
        self.name = name

    @abc.abstractmethod
    def create_output(self):
        pass

    @abc.abstractmethod
    def write_row(self, meta, feat, text=None):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @staticmethod
    def _get_index(length, value):
        if value < 0:
            return 0
        return min(value, length)
