import logging

import pyodbc
from jinja2 import Template

from pytakes.io import templates
from pytakes.io.base import Dictionary, Output, Document
from pytakes.processor import TextItem


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
        :param dbi:
        :param term_table:
        :param valence:
        :param regex_variation:
        :param word_order:
        """
        logging.info('Getting Terms and Negation.')
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

    def __init__(self, dbi=None, schema=None, where_clause=None,
                 order_by=None, batch_size=None, meta=None,
                 text=None, **config):
        super().__init__(**config)
        self.text = text
        self.meta = meta
        self.dbi = dbi
        if schema:
            self.fullname = '{}.{}'.format(schema, self.name)
        self.order_by = order_by
        self.batch_size = batch_size
        self.where_clause = where_clause

    def read_next(self):
        """
        Retrieve documents from table
        :param meta_labels:
        :param text_labels:
        :param where_clause:
        :param order_by:
        :param batch_size:
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
        self.hostname = hostname
        self.batch_number = batch_number
        self.force = force
        if schema:
            self.fullname = '{}.{}'.format(schema, self.name)

    def close(self):
        pass

    def delete_table_rows(self):
        """Drop all rows from destination table.

        :param dbi:
        :param destination_table:
        :return:
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


    def write_row(self, meta, feat, text=None):
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
