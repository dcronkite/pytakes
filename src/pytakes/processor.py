"""

Edit:
2013-12-24    added line-ending splitting
2013-12-05    added begin/end offsets for conceptminer2
2013-11-26    added option for conceptminer2
"""

import argparse
import logging
import logging.config
import math
import pyodbc
import sys

from util import mylogger
from util.nlp import conceptminer as miner
from util.nlp.ngrams import FeatureMiner
from util.nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp import conceptminer2 as miner2
from pytakes.util.db_reader import DbInterface


class Document(object):
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
    """
    sql = "SELECT %s FROM %s" % (table_id, document_table)
    sql += order_by
    document_ids = dbi.execute_fetchall(sql)
    return [x[0] for x in document_ids]  # remove lists


def get_documents(dbi, document_table, meta_labels, text_labels, where_clause, order_by, batch_size):
    """
    Retrieve documents from table
    """
    sql = "SELECT "
    if where_clause and order_by:
        sql += ' TOP %d ' % batch_size
    sql += ','.join([x for x in meta_labels])
    sql += "," + ','.join(text_labels)
    sql += " FROM " + document_table
    sql += ' ' + where_clause + order_by
    document_list = dbi.execute_fetchall(sql)
    result_list = []
    for row in document_list:
        doc = Document(row[:-len(text_labels)], row[-len(text_labels):])
        result_list.append(doc)
    return result_list


def get_terms(dbi, term_table, valence=None, regex_variation=None, word_order=None):
    """
    Retrieve terms from table.
    Function checks to see if optional columns are present,
    otherwise uses cTAKES defaults.
    """
    logging.info('Getting Terms and Negation.')
    columns = dbi.get_table_columns(term_table.split('.')[-1])  # if [dbo] or [MASTER\...] prefaced to tablename
    columns = [x[0].lower() for x in columns]
    valence = valence if valence else '' if 'valence' in columns else '1 as'
    regex_variation = regex_variation if regex_variation else '' if 'regexvariation' in columns else '3 as'
    word_order = word_order if word_order else '' if 'WordOrder' in columns else '1 as' #changed wordorder to WordOrder

    return dbi.execute_fetchall('''
        SELECT id
             , text
             , cui
             , %s valence
             , %s regex_variation
             , %s word_order
        FROM %s
    ''' % (valence, regex_variation, word_order, term_table))


def get_negex(dbi, neg_table):
    """
    Retrieve negation triggers from table
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
             FROM %s
    ''' % neg_table)


def get_context(dbi, neg_table):
    """
    Retrieve negation triggers from table.
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
                 , direction
             FROM %s
    ''' % neg_table)


def create_table(dbi, destination_table, labels, types):
    """

    """
    sql = "CREATE TABLE %s ( rowid int IDENTITY(1,1) PRIMARY KEY, " % destination_table
    sql += ','.join([x + ' ' + y for x, y in zip(labels, types)])
    sql += ")"
    logging.debug(sql)
    dbi.execute_commit(sql)


def delete_table_rows(dbi, destination_table):
    """Drop all rows from destination table.

    :param dbi:
    :param destination_table:
    :return:
    """
    sql = "TRUNCATE TABLE {}".format(destination_table)
    logging.debug(sql)
    dbi.execute_commit(sql)


def insert_into(dbi, destination_table, feat, text, labels, meta):
    """

    """
    sql = "INSERT INTO %s (" % destination_table
    sql += ','.join(labels) + ') VALUES ('
    sql += '\'' + "','".join([str(x) for x in meta]) + '\','
    sql += (" %d, '%s', '%s', %d, %d)" %
            (feat.id(),
             text[feat.begin():feat.end()].strip(),
             text[get_index(len(text), feat.begin() - 75):
             get_index(len(text), feat.end() + 75)],
             0 if feat.is_negated() else 1,
             0 if feat.is_possible() else 1))
    dbi.execute_commit(sql)


def insert_into2(dbi, destination_table, feat, text, labels, meta):
    """

    """
    sql = "INSERT INTO %s (" % destination_table
    sql += ','.join(labels) + ') VALUES ('
    sql += '\'' + "','".join([str(x) for x in meta]) + '\','
    sql += (" %d, '%s', '%s', '%s', %d, %d, %d, %d, %d, %d, %d, %d)" %
            (feat.id(),
             text[feat.begin():feat.end()].strip(),
             text[get_index(len(text), feat.begin() - 75):
             get_index(len(text), feat.end() + 75)],
             text,
             feat.get_certainty(),
             1 if feat.is_hypothetical() else 0,
             1 if feat.is_historical() else 0,
             1 if feat.is_not_patient() else 0,
             feat.begin(),
             feat.end(),
             feat.get_absolute_begin(),
             feat.get_absolute_end()))
    dbi.execute_commit(sql)


def insert_into3(dbi, destination_table, feat, labels, meta):
    """
    Insert ngram features into database.
    :param dbi:
    :param destination_table:
    :param feat:
    :param labels:
    :param meta:
    :return:
    """
    sql = "INSERT INTO %s (" % destination_table
    sql += ','.join(labels) + ') VALUES ('
    sql += '\'' + "','".join([str(x) for x in meta]) + '\','
    sql += " {}, '{}', '{}'".format(feat.get_id(), feat.get_feature(), feat.get_category())
    sql += ')'
    dbi.execute_commit(sql)


def get_index(length, value):
    if value < 0:
        return 0
    return min(value, length)


def process(dbi, mc, sb, destination_table, document_table, meta_labels, text_labels, concept_miner_v, all_labels,
            where_clause, order_by, batch_size, mine_options):
    """

    """
    logging.info('Retrieving notes.')
    documents = get_documents(dbi, document_table, meta_labels, text_labels, where_clause, order_by, batch_size)
    length = len(documents)
    logging.info('Retrieved %d notes.' % length)

    pct = 5

    for num, doc in enumerate(documents):
        if 100 * (float(num) / length) > pct:
            logging.info('Completed %d%%.' % int(pct))
            pct += 5

        # adding sentence splitting (2013-11-08)
        sentences = []
        for section in sb.ssplit(doc.get_text()):
            sentences += section.split('\n')

        if concept_miner_v == 1 or concept_miner_v == 2:
            sections = mc.mine(sentences, **mine_options)
        elif concept_miner_v == 3:
            sections = mc.mine(sentences)  # mine_options passed to ctor
        else:
            raise ValueError('Concept Miner v.%d is not defined.' % concept_miner_v)

        for sect_num, sect in enumerate(sections):
            if not sect:
                continue
            for feat in sect:
                if concept_miner_v == 1:
                    insert_into(dbi, destination_table, feat, mc.prepare(sentences[sect_num]), all_labels,
                                doc.get_metalist())
                elif concept_miner_v == 2:
                    insert_into2(dbi, destination_table, feat, mc.prepare(sentences[sect_num]), all_labels,
                                 doc.get_metalist())
                elif concept_miner_v == 3:
                    insert_into3(dbi, destination_table, feat, all_labels, doc.get_metalist())
                else:
                    raise ValueError('Concept Miner v.%d is not defined.' % concept_miner_v)


def prepare(term_table, neg_table, neg_var, document_table, meta_labels, text_labels, concept_miner_v,
            destination_table, batch_mode, batch_size, batch_number, db_options, mine_options, terms_options, force):
    """

    """
    dbi = DbInterface(**db_options)

    all_types = ['varchar(255)'] * len(meta_labels)
    all_labels = list(meta_labels)

    if concept_miner_v == 1:
        negation_tuples = get_negex(dbi, neg_table)
        concept_entries = get_terms(dbi, term_table, **terms_options)
        mc = miner.MinerCask(concept_entries, negation_tuples, neg_var)
        all_labels += ['id', 'captured', 'context', 'polarity', 'certainty']
        all_types += ['int', 'varchar(255)', 'varchar(255)', 'int', 'int']

    elif concept_miner_v == 2:
        negation_tuples = get_context(dbi, neg_table)
        concept_entries = get_terms(dbi, term_table, **terms_options)
        mc = miner2.MinerCask(concept_entries, negation_tuples, neg_var)
        all_labels += ['dictid', 'captured', 'context', 'text', 'certainty', 'hypothetical', 'historical',
                       'otherSubject', '"start"', '"finish"', 'start_idx', 'end_idx']
        all_types += ['int', 'varchar(255)', 'varchar(255)', 'varchar(max)', 'int',
                      'int', 'int', 'int', 'int', 'int', 'int', 'int']

    elif concept_miner_v == 3:
        all_labels += ['featid', 'feature', 'category']
        all_types += ['bigint', 'varchar(max)', 'varchar(50)']
        mc = FeatureMiner(**mine_options)

    else:
        raise ValueError('Invalid version for ConceptMiner: %d.' % concept_miner_v)

    # if batch mode, select all ids, and split into batches
    if batch_mode:
        order_by = ' ORDER BY %s ' % batch_mode
        doc_ids = get_document_ids(dbi, document_table, batch_mode, order_by)
        # get minimum value of each batch size
        batches = [doc_ids[x * batch_size]
                   for x in range(int(math.ceil(float(len(doc_ids)) / batch_size)))]
    else:
        batches = [None]
        order_by = ''

    batch_length = len(batches)
    logging.info('Prepared %d batch(es).' % batch_length)
    for curr_batch, batch in enumerate(batches, 1):
        if batch_mode and batch_number and curr_batch not in batch_number:
            continue

        # create table
        dest_table = '{}_{}'.format(destination_table, curr_batch)
        try:
            create_table(dbi, dest_table, all_labels, all_types)
            logging.info('Table created: %s.' % dest_table)
        except pyodbc.ProgrammingError as pe:
            logging.warning('Table already exists.')
            if force:
                logging.warning('Force deleting rows from table {}.'.format(dest_table))
                delete_table_rows(dbi, dest_table)
            else:
                logging.error('Add option "force" to delete rows from table.')
                sys.exit(1)
        except Exception as e:
            logging.exception(e)
            logging.error('Failed to create table.')
            raise e

        logging.info('Started batch #%d (ending at %d).' % (curr_batch, batch_number[-1] if batch_number else 1))

        if batch_mode:
            where_clause = ' WHERE %s > %d ' % (batch_mode, batch)
        else:
            where_clause = ''
        process(dbi, mc, SentenceBoundary(dbi), dest_table, document_table, meta_labels, text_labels,
                concept_miner_v, all_labels, where_clause, order_by, batch_size, mine_options)
        logging.info('Finished batch #%d of %d.' % (curr_batch, batch_length))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--term-table', help='cTAKES Dictionary Lookup table.')
    parser.add_argument('--negation-table', help='Table of negation triggers, along with role.')
    parser.add_argument('--negation-variation', type=int, default=0, required=False,
                        help='Amount of variation to allow in negations. Values: 0-3.')
    parser.add_argument('--document-table', help='Table with text field.')
    parser.add_argument('--meta-labels', nargs='+', help='Extra identifying labels to include in output.')
    parser.add_argument('--text-label', help='Name of text column.')  # for backwards compatibility
    parser.add_argument('--text-labels', nargs='+', help='Name of text columns.')
    parser.add_argument('--destination-table', help='Output table. Should not exist.')
    parser.add_argument('--concept-miner', default=1, type=int, help='Version of ConceptMiner to use.')
    parser.add_argument('--batch-mode', help='Specify Identity column.')
    parser.add_argument('--batch-size', nargs='?', default=100000, const=100000, type=int,
                        help='Process documents in batch mode. Optionally specify batch size.')
    parser.add_argument('--batch-number', nargs='+', type=int, help='Specify a certain batch to do.')

    parser.add_argument('--verbosity', type=int, default=2, help='Verbosity of log output.')

    parser.add_argument('--driver', required=False, default='SQL Server')
    parser.add_argument('--server', required=False, default='ghrinlp')
    parser.add_argument('--database', required=False, default='nlpdev')
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

    term_table = args.term_table  # 'COT_Dict_Clin_Lab_Abuse_09Aug2013'
    neg_table = args.negation_table
    neg_var = args.negation_variation
    document_table = args.document_table  # 'vCOT_Clinabuse_data'
    meta_labels = args.meta_labels  # ['ft_id', 'chsid']
    if args.text_labels:
        text_labels = args.text_labels
    elif args.text_label:
        text_labels = [args.text_label]
        logging.warning('WARNING: Using deprecated option, --text-label; change to --text-labels.')
    else:
        raise ValueError('No text labels provided.')

    concept_miner_v = args.concept_miner
    destination_table = args.destination_table  # 'COT_LOCAL_Clinabuse_out_20131020'
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
                mine_options, terms_options, args.force)
    except Exception as e:
        import traceback

        logging.info(traceback.format_exc())
        logging.error(e)
        sys.exit(1)  # this will signal a batch file
    sys.exit(0)
