"""

Edit:
2013-12-24    added line-ending splitting
2013-12-05    added begin/end offsets for conceptminer2
2013-11-26    added option for conceptminer2
"""

import argparse
import logging
import logging.config
import pyodbc
import sys
from socket import gethostname
from typing import List

from jinja2 import Template

from pytakes import templates
from pytakes.io.base import Document, Dictionary, Output
from pytakes.parser import parse_processor
from pytakes.util.utils import flatten
from .util import mylogger
from .nlp.ngrams import FeatureMiner
from .nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp import conceptminer2 as miner2


class TextItem(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, meta_list, text):
        self.meta_ = meta_list
        if isinstance(text, str):
            text = [text]
        else:
            text = [t for t in text if t]
        try:
            self.text_ = self.fix_text(text[0])
        except IndexError as e:
            self.text_ = ""
        for txt in text[1:]:
            self.add_text(txt)  # split added 20131224

    def add_text(self, text):
        self.text_ += '\n' + self.fix_text(text)

    def get_text(self):
        return self.text_

    def get_metalist(self):
        return self.meta_

    def fix_text(self, text):
        text = ' '.join(text.split('\n'))
        text.replace('don?t', "don't")  # otherwise the '?' will start a new sentence
        return text


def get_document_ids(dbi, document_table, table_id, order_by):
    """
    Retrieve documents from table (for batch mode)
    :param dbi:
    :param document_table:
    :param table_id:
    :param order_by:
    """
    dbi.execute(Template(templates.PROC_GET_DOC_IDS).render({
        'table_id': table_id,
        'doc_table': document_table,
        'order_by': order_by
    }))
    return [x[0] for x in dbi]  # remove lists


def get_documents(dbi, document_table, meta_labels, text_labels, where_clause, order_by, batch_size):
    """
    Retrieve documents from table
    :param dbi:
    :param document_table:
    :param meta_labels:
    :param text_labels:
    :param where_clause:
    :param order_by:
    :param batch_size:
    """
    sql = Template(templates.PROC_GET_DOCS).render({
        'where_clause': where_clause,
        'order_by': order_by,
        'batch_size': batch_size,
        'meta_labels': meta_labels,
        'text_labels': text_labels,
        'doc_table': document_table
    })
    dbi.execute(sql)
    result_list = []
    for row in dbi:
        doc = TextItem(row[:-len(text_labels)], row[-len(text_labels):])
        result_list.append(doc)
    return result_list


def get_terms(dbi, term_table, valence=None, regex_variation=None, word_order=None):
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
    columns = dbi.get_table_columns(term_table.split('.')[-1])  # if [dbo] or [MASTER\...] prefaced to tablename
    columns = [x[0].lower() for x in columns]

    try:
        return dbi.execute_fetchall(Template(templates.PROC_GET_TERMS).render({
            'columns': columns,
            'valence': valence,
            'regex_variation': regex_variation,
            'word_order': word_order,
            'term_table': term_table
        }))
    except pyodbc.ProgrammingError as pe:
        logging.exception(pe)
        logging.error('Ensure that the term table has the variables "id", "text", and "cui".')
        raise pe


def create_table(dbi, destination_table, labels, types):
    """
    :param dbi:
    :param destination_table:
    :param labels:
    :param types:

    """
    dbi.execute_commit(Template(templates.PROC_CREATE_TABLE).render({
        'destination_table': destination_table,
        'labels_types': zip(labels, types)
    }))


def delete_table_rows(dbi, destination_table):
    """Drop all rows from destination table.

    :param dbi:
    :param destination_table:
    :return:
    """
    sql = "TRUNCATE TABLE {}".format(destination_table)
    logging.debug(sql)
    dbi.execute_commit(sql)


def insert_into2(dbi, destination_table, feat, text, labels, meta, hostname, batch_number):
    """
    :param dbi:
    :param destination_table:
    :param feat:
    :param text:
    :param labels:
    :param meta:
    :param hostname:
    :param batch_number:
    """
    dbi.execute_commit(
        Template(templates.PROC_INSERT_INTO2_QUERY).render(
            labels=labels, metas=meta,
            destination_table=destination_table, feature=feat, text=text,
            captured=text[feat.begin():feat.end()].strip(),
            context=text[get_index(len(text), feat.begin() - 75):get_index(len(text), feat.end() + 75)],
            hostname=hostname, batch_number=batch_number
        )
    )


def insert_into3(dbi, destination_table, feat, labels, meta, hostname, batch_number):
    """
    Insert ngram features into database.
    :param batch_number:
    :param hostname:
    :param dbi:
    :param destination_table:
    :param feat:
    :param labels:
    :param meta:
    :return:
    """
    dbi.execute_commit(
        Template(templates.PROC_INSERT_INTO3_QUERY).render(
            labels=labels, metas=meta,
            destination_table=destination_table, feature=feat,
            hostname=hostname, batch_number=batch_number
        )
    )


def get_index(length, value):
    if value < 0:
        return 0
    return min(value, length)


def process(documents: List[Document], outputs: List[Output], mc, sb):
    """
    :param outputs:
    :param documents:
    :param mc:
    :param sb:

    """
    logging.info('Retrieving notes.')
    documents = (doc.read() for doc in documents)

    for document in documents:
        for num, doc in enumerate(document.read_next()):
            if num % 100 == 0:
                logging.info('Completed: {:>5}.'.format(num))

            sentences = []
            for section in sb.ssplit(doc.get_text()):
                sentences += section.split('\n')

            for sect_num, sect in enumerate(mc.mine(sentences)):
                if not sect:
                    continue
                for feat in sect:
                    for out in outputs:
                        out.writerow(doc.get_metalist(), feat, text=doc.get_text())
    logging.info('Completed: 100%')


def prepare(documents: List[Document], dictionaries: List[Dictionary],
            outputs: List[Output], negation_dicts: List[Dictionary], concept_miner_v,
            batch_mode, batch_size, batch_number,
            tracking_method):
    """
    :param documents:
    :param dictionaries:
    :param outputs:
    :param negation_dicts:
    :param concept_miner_v:
    :param batch_mode:
    :param batch_size:
    :param batch_number:
    :param tracking_method:

    """
    if concept_miner_v in [1, 2]:
        negation_tuples = list(flatten(d.read() for d in negation_dicts))
        concept_entries = list(flatten(d.read() for d in dictionaries))
        mc = miner2.MinerCask(concept_entries, negation_tuples)

    elif concept_miner_v == 3:
        mc = FeatureMiner()

    else:
        raise ValueError('Invalid version for ConceptMiner: %d.' % concept_miner_v)

    for out in outputs:
        out.create_output()

    process(documents, outputs, mc, SentenceBoundary())


def main_json():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--json-config',
                        help='Json file containing configuration information.')
    args = parser.parse_args()
    parse_processor(args.json_config)


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--term-table', help='cTAKES Dictionary Lookup table.')
    parser.add_argument('--negation-table', help='Table of negation triggers, along with role.')
    parser.add_argument('--negation-variation', type=int, default=0, required=False,
                        help='Amount of variation to allow in negations. Values: 0-3.')
    parser.add_argument('--document-table', help='Table with text field.')
    parser.add_argument('--meta-labels', nargs='+', help='Extra identifying labels to include in output.')
    parser.add_argument('--text-labels', nargs='+', help='Name of text columns.')
    parser.add_argument('--destination-table', help='Output table. Should not exist.')
    parser.add_argument('--concept-miner', default=2, type=int, help='Version of ConceptMiner to use.')
    parser.add_argument('--batch-mode', help='Specify Identity column.')
    parser.add_argument('--batch-size', nargs='?', default=100000, const=100000, type=int,
                        help='Process documents in batch mode. Optionally specify batch size.')
    parser.add_argument('--batch-number', nargs='+', type=int, help='Specify a certain batch to do.')

    parser.add_argument('--tracking-method', choices=['name', 'column'], default='name',
                        help='Method to track progress of batches.')

    parser.add_argument('--verbosity', type=int, default=2, help='Verbosity of log output.')

    parser.add_argument('--driver', required=False, default='SQL Server')
    parser.add_argument('--server', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--max-intervening-terms', required=False, default=1, type=int)
    parser.add_argument('--max-length-of-search', required=False, default=3, type=int)
    parser.add_argument('--valence', required=False, default=None, type=int)
    parser.add_argument('--regex-variation', required=False, default=None, type=int)
    parser.add_argument('--word-order', required=False, default=None, type=int)

    parser.add_argument('--force', action='store_true', default=False,
                        help='Force delete rows in table.')

    # for concept miner version 3
    parser.add_argument('--stopwords', required=False, default=[], nargs='+',
                        help='List of words to skip over when collecting features. Does not support regexes.')
    parser.add_argument('--exclusion-patterns', required=False, default=[], nargs='+',
                        help='List of regex patterns which eliminate features matching the regex.')
    parser.add_argument('--number-normalization', required=False, default=False, action='store_true',
                        help='Normalize all numbers to a standard feature regardless of their value.')

    args = parser.parse_args()

    term_table = args.term_table
    neg_table = args.negation_table
    neg_var = args.negation_variation
    document_table = args.document_table
    meta_labels = args.meta_labels
    if args.text_labels:
        text_labels = args.text_labels
    else:
        raise ValueError('No text labels provided.')

    concept_miner_v = args.concept_miner
    destination_table = args.destination_table
    batch_mode = args.batch_mode
    batch_size = args.batch_size
    batch_number = args.batch_number

    loglevel = mylogger.resolve_verbosity(args.verbosity)

    if batch_mode and batch_number and len(batch_number) > 1:
        batch_number.sort()
        batch_number = list(range(batch_number[0], batch_number[-1]))

        logging.config.dictConfig(mylogger.setup('pytakes-processor' + str(batch_number[0]), loglevel=loglevel))
    else:
        logging.config.dictConfig(mylogger.setup('pytakes-processor', loglevel=loglevel))

    try:
        terms_options = {'valence': args.valence,
                         'regex_variation': args.regex_variation,
                         'word_order': args.word_order}
        db_options = {'driver': args.driver,
                      'server': args.server,
                      'database': args.database}
        if concept_miner_v == 1 or concept_miner_v == 2:
            mine_options = {'max_length_of_search': args.max_length_of_search,
                            'max_intervening_terms': args.max_intervening_terms}
        elif concept_miner_v == 3:
            mine_options = {'stopwords': args.stopwords,
                            'patterns': args.exclusion_patterns,
                            'number_norm': args.number_normalization}
        else:
            raise ValueError('Concept Miner v.%d is not defined.' % concept_miner_v)
        prepare(term_table, neg_table, neg_var, document_table, meta_labels, text_labels, concept_miner_v,
                destination_table, batch_mode, batch_size, batch_number, db_options,
                mine_options, terms_options, args.force, args.tracking_method)
    except Exception as e:
        import traceback

        logging.info(traceback.format_exc())
        logging.error(e)
        sys.exit(1)  # this will signal a batch file
    sys.exit(0)  # required if called from script, otherwise results in 'Failed' message

if __name__ == '__main__':
    main()
