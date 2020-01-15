"""
Base classes for interface.
"""
import abc


class Dictionary(metaclass=abc.ABCMeta):
    def __init__(self, name=None, **kwargs):
        self.name = name

    @abc.abstractmethod
    def read(self):
        pass

    def int_or_default(self, val, default):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default


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
    all_labels = ['dictid', 'concept', 'captured', 'context', 'certainty', 'hypothetical', 'historical',
                  'otherSubject', 'start_idx', 'end_idx', 'cpu_name', 'version']
    all_types = ['int', 'varchar(50)', 'varchar(255)', 'varchar(255)', 'int', 'int', 'int',
                 'int', 'int', 'int', 'varchar(50)', 'int']

    def __init__(self, name=None, context_width=75, **config):
        self.name = name
        self.context_width = context_width

    def __enter__(self):
        return self

    @abc.abstractmethod
    def writerow(self, feat, meta=None, text=None):
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def _get_index(length, value):
        if value < 0:
            return 0
        return min(value, length)

    @staticmethod
    def _get_text(text, start, end, remove_newlines=True):
        if remove_newlines:
            return ' '.join(text[start:end].split('\n'))
        else:
            return text[start:end]
