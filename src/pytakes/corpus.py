import itertools
import os
from typing import Iterable

from pytakes import TextItem
from pytakes.iolib import sqlai


def get_next_from_directory(directories=None, encoding='utf8'):
    for directory in directories or ():
        for root, dirs, files in os.walk(directory):
            for file in files:
                fp = os.path.join(directory, file)
                try:
                    with open(fp, encoding=encoding) as fh:
                        text = fh.read()
                except FileNotFoundError:
                    continue
                else:
                    yield '.'.join(file.split('.')[:-1]) or file, text


def get_next_from_connections(*connections):
    for connection in connections:
        for doc_name, text in get_next_from_sql(**connection):
            yield doc_name, text


def get_next_from_sql(name=None, driver=None, server=None,
                      database=None, connection_string=None,
                      name_col=None, text_col=None):
    """
    :param name_col:
    :param text_col:
    :param name: tablename (if connecting to database)
    :param driver: db driver  (if connecting to database)
    :param server: name of server (if connecting to database)
    :param database: name of database (if connecting to database)
    """
    if name and driver and server and database:
        eng = sqlai.get_engine(connection_string=connection_string, driver=driver, server=server, database=database)
        for doc_name, text in eng.execute(f'select {name_col}, {text_col} from {name}'):
            yield doc_name, text


def get_next_from_corpus(*dirs, directories=None, encoding='utf8', connections=None) -> Iterable[TextItem]:
    for doc_name, text in itertools.chain(
            get_next_from_directory(dirs, encoding),
            get_next_from_directory(directories, encoding),
            get_next_from_connections(*connections or list())
    ):
        yield TextItem(text.split('\n\n'), file=doc_name)  # force new sentence with double-newline