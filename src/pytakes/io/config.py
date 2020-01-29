from .csv import CsvDictionary, CsvDocument, CsvOutput
from .sas import SasDictionary, SasDocument
from .sql import SqlDictionary, SqlDocument, SqlOutput

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