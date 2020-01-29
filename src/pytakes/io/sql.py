import logging
import platform

import pyodbc
from jinja2 import Template

from . import templates
from .base import Dictionary, Output, Document
from ..dict.textitem import TextItem


class SqlDictionary(Dictionary):

    def __init__(self, dbi=None, schema=None, valence=None,
                 regex_variation=None, word_order=None, **kwargs):
        super().__init__(**kwargs)
        self.dbi = dbi
        self.valence = valence
        self.regex_variation = regex_variation
        self.word_order = word_order
        if schema:
            self.fullname = '{}.{}'.format(schema, self.name)

    def read(self):
        return self._get_terms()

    def _get_terms(self):
        """
        Retrieve terms from table.
        Function checks to see if optional columns are present,
        otherwise uses cTAKES defaults.
        """
        logging.info('Getting Terms.')
        # if [dbo] or [MASTER\...] prefaced to tablename
        columns = (x.lower() for x in self.dbi.get_table_columns(self.name))

        try:
            return self.dbi.execute_fetchall(Template(templates.PROC_GET_TERMS).render({
                'columns': columns,
                'valence': self.valence,
                'regex_variation': self.regex_variation,
                'word_order': self.word_order,
                'term_table': self.fullname
            }))
        except pyodbc.ProgrammingError as pe:
            logging.exception(pe)
            logging.error('Ensure that the term table has the variables "id", "text", and "cui".')
            raise pe


class SqlDocument(Document):

    def get_ids(self):
        """
        Retrieve documents from table (for batch mode)
        """
        self.dbi.execute(Template(templates.PROC_GET_DOC_IDS).render({
            'table_id': self.meta[0],
            'doc_table': self.fullname,
            'order_by': self.order_by
        }))
        return (x[0] for x in self.dbi)  # remove lists

    def __len__(self):
        pass

    def __init__(self, dbi=None, schema=None, where_clause=None,
                 order_by=None, batch_size=None, meta=None,
                 text=None, batch_mode=None, **config):
        super().__init__(**config)
        self.text = text
        self.meta = meta
        self.dbi = dbi
        if schema:
            self.fullname = '{}.{}'.format(schema, self.name)
        self.order_by = order_by
        self.batch_size = batch_size
        self.where_clause = '{} > {}'.format(self.meta[0], batch_mode)

    def read_next(self):
        """
        Retrieve documents from table
        """
        sql = Template(templates.PROC_GET_DOCS).render({
            'where_clause': self.where_clause,
            'order_by': self.order_by,
            'batch_size': self.batch_size,
            'meta_labels': self.meta,
            'text_labels': self.text,
            'doc_table': self.fullname
        })
        self.dbi.execute(sql)
        for row in self.dbi:
            yield TextItem(row[:-len(self.text)], row[-len(self.text):])


class SqlOutput(Output):

    def __init__(self, dbi=None, schema=None, labels=None,
                 types=None, hostname=None, batch_number=None, force=False, **config):
        super().__init__(**config)
        self.dbi = dbi
        self.labels = labels
        self.types = types
        self.hostname = hostname or platform.node()
        self.batch_number = batch_number
        self.force = force
        self.fullname = self.name
        if schema:
            self.fullname = '{}.{}'.format(schema, self.fullname)
        if batch_number:
            self.fullname = '{}_{}'.format(self.fullname, batch_number)

    def close(self):
        self.dbi.close()

    def delete_table_rows(self):
        """Drop all rows from destination table.

        :return: None
        """
        sql = "TRUNCATE TABLE {}".format(self.fullname)
        logging.debug(sql)
        self.dbi.execute_commit(sql)

    def create_output(self):
        try:
            self.dbi.execute_commit(Template(templates.PROC_CREATE_TABLE).render({
                'destination_table': self.fullname,
                'labels_types': zip(self.labels, self.types)
            }))
            logging.info('Table created: %s.' % self.fullname)
        except pyodbc.ProgrammingError as pe:
            logging.warning('Table already exists.')
            logging.error(pe)
            if self.force:
                logging.warning('Force deleting rows from table {}.'.format(self.fullname))
                self.delete_table_rows()
            else:
                logging.error('Add option "force" to delete rows from table.')
                raise pe
        except Exception as e:
            logging.exception(e)
            logging.error('Failed to create table.')
            raise e

    def writerow(self, meta, feat, text=None):
        self.dbi.execute_commit(
            Template(templates.PROC_INSERT_INTO2_QUERY).render(
                labels=self.labels, metas=meta,
                destination_table=self.fullname, feature=feat, text=text,
                captured=text[feat.begin():feat.end()].strip(),
                context=text[self._get_index(len(text), feat.begin() - 75):self._get_index(len(text), feat.end() + 75)],
                hostname=self.hostname, batch_number=self.batch_number
            )
        )
        self.dbi.execute_commit(
            Template(templates.PROC_INSERT_INTO3_QUERY).render(
                labels=self.labels, metas=meta,
                destination_table=self.fullname, feature=feat,
                hostname=self.hostname, batch_number=self.batch_number
            )
        )
