"""

Edit:
2013-12-24    added line-ending splitting
2013-12-05    added begin/end offsets for conceptminer2
2013-11-26    added option for conceptminer2
"""

import argparse
from itertools import izip
import logging
import logging.config
import math
import pyodbc
import sys

from ghri.db_reader import dbInterface
from ghri.nlp import conceptminer as miner
from ghri.nlp import conceptminer2 as miner2
from ghri.nlp.sentence_boundary import SentenceBoundary
from ghri import mylogger


class Document(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, meta_list, text):
        self.meta_ = meta_list
        if isinstance(text, basestring):
            text = [text]
        else:
            text = [t for t in text if t]
        self.text_ = self.fixText(text[0])
        for txt in text[1:]:
            self.addText(txt)  # split added 20131224

    def addText(self, text):
        self.text_ += '\n' + self.fixText(text)

    def getText(self):
        return self.text_

    def getMetaList(self):
        return self.meta_

    def fixText(self, text):
        text = ' '.join(text.split('\n'))
        text.replace('don?t', "don't")  # otherwise the '?' will start a new sentence
        return text


def getDocumentIds(dbi, document_table, table_id, order_by):
    """
    Retrieve documents from table (for batch mode)
    """
    sql = "SELECT %s FROM %s" % (table_id, document_table)
    sql += order_by
    document_ids = dbi.execute_fetchall(sql)
    return [x[0] for x in document_ids]  # remove lists


def getDocuments(dbi, document_table, meta_labels, text_labels, where_clause, order_by, batch_size):
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


def getTerms(dbi, term_table, valence=None, regexVariation=None, wordOrder=None):
    """
    Retrieve terms from table.
    Function checks to see if optional columns are present,
    otherwise uses cTAKES defaults.
    """
    columns = dbi.execute_fetchall('''
        SELECT column_name
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '%s'
        ''' % term_table.split('.')[-1])  # if [dbo] or [MASTER\...] prefaced to tablename
    columns = [x[0].lower() for x in columns]
    valence = valence if valence else '' if 'valence' in columns else '1 as'
    regexVariation = regexVariation if regexVariation else '' if 'regexvariation' in columns else '3 as'
    wordOrder = wordOrder if wordOrder else '' if 'wordorder' in columns else '1 as'

    return dbi.execute_fetchall('''
        SELECT id
             , text
             , cui
             , %s valence
             , %s regexVariation
             , %s wordOrder
        FROM %s
    ''' % (valence, regexVariation, wordOrder, term_table))


def getNegex(dbi, neg_table):
    """
    Retrieve negation triggers from table
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
             FROM %s
    ''' % neg_table)


def getContext(dbi, neg_table):
    """
    Retrieve negation triggers from table.
    """
    return dbi.execute_fetchall('''
            SELECT negex
                 , type
                 , direction
             FROM %s
    ''' % neg_table)


def createTable(dbi, destination_table, labels, types):
    """

    """
    sql = "CREATE TABLE %s ( rowid int IDENTITY(1,1) PRIMARY KEY, " % destination_table
    sql += ','.join([x + ' ' + y for x, y in izip(labels, types)])
    sql += ")"
    logging.debug(sql)
    dbi.execute_commit(sql)


def insertInto(dbi, destination_table, feat, text, labels, meta):
    """

    """
    sql = "INSERT INTO %s (" % destination_table
    sql += ','.join(labels) + ') VALUES ('
    sql += '\'' + "','".join([str(x) for x in meta]) + '\','
    sql += (" %d, '%s', '%s', %d, %d)" %
            (feat.id(),
             text[feat.begin():feat.end()].strip(),
             text[getIndex(len(text), feat.begin() - 75):
             getIndex(len(text), feat.end() + 75)],
             0 if feat.isNegated() else 1,
             0 if feat.isPossible() else 1))
    dbi.execute_commit(sql)


def insertInto2(dbi, destination_table, feat, text, labels, meta):
    """

    """
    sql = "INSERT INTO %s (" % destination_table
    sql += ','.join(labels) + ') VALUES ('
    sql += '\'' + "','".join([str(x) for x in meta]) + '\','
    sql += (" %d, '%s', '%s', '%s', %d, %d, %d, %d, %d, %d, %d, %d)" %
            (feat.id(),
             text[feat.begin():feat.end()].strip(),
             text[getIndex(len(text), feat.begin() - 75):
             getIndex(len(text), feat.end() + 75)],
             text,
             feat.getCertainty(),
             1 if feat.isHypothetical() else 0,
             1 if feat.isHistorical() else 0,
             1 if feat.isNotPatient() else 0,
             feat.begin(),
             feat.end(),
             feat.getAbsoluteBegin(),
             feat.getAbsoluteEnd()))
    dbi.execute_commit(sql)


def getIndex(length, value):
    if value < 0:
        return 0
    elif value > length:
        return length
    else:
        return value


def process(dbi, mc, sb, destination_table, document_table, meta_labels, text_labels, concept_miner_v, all_labels,
            where_clause, order_by, batch_size, max_intervening_terms, max_length_of_search):
    """

    """
    logging.info('Retrieving notes.')
    documents = getDocuments(dbi, document_table, meta_labels, text_labels, where_clause, order_by, batch_size)
    LENGTH = len(documents)
    logging.info('Retrieved %d notes.' % LENGTH)

    pct = 5

    for num, doc in enumerate(documents):
        if 100 * (float(num) / LENGTH) > pct:
            logging.info('Completed %d%%.' % int(pct))
            pct += 5

        # adding sentence splitting (2013-11-08)
        sentences = []
        for section in sb.ssplit(doc.getText()):
            sentences += section.split('\n')

        sections = mc.mine(sentences, max_intervening_terms=max_intervening_terms,
                           max_length_of_search=max_length_of_search)
        for sect_num, sect in enumerate(sections):
            if not sect: continue
            text = mc.prepare(sentences[sect_num])
            for feat in sect:
                if concept_miner_v == 1:
                    insertInto(dbi, destination_table, feat, text, all_labels, doc.getMetaList())
                elif concept_miner_v == 2:
                    insertInto2(dbi, destination_table, feat, text, all_labels, doc.getMetaList())
                else:
                    raise ValueError('Concept Miner v.%d is not defined.' % concept_miner_v)


def prepare(term_table, neg_table, neg_var, document_table, meta_labels, text_labels, concept_miner_v,
            destination_table, batch_mode, batch_size, batch_number, server, database, max_intervening_terms,
            max_length_of_search, valence, regex_variation, word_order):
    """

    """
    dbi = dbInterface('SQL Server', server, database)
    logging.info('Getting Terms and Negation.')
    concept_entries = getTerms(dbi, term_table, valence=valence, regexVariation=regex_variation, wordOrder=word_order)

    if concept_miner_v == 1:
        negation_tuples = getNegex(dbi, neg_table)
        mc = miner.MinerCask(concept_entries, negation_tuples, neg_var)
        all_labels = meta_labels + ['id', 'captured', 'context', 'polarity', 'certainty']
        all_types = ['varchar(255)'] * len(meta_labels) + ['int', 'varchar(255)', 'varchar(255)', 'int', 'int']

    elif concept_miner_v == 2:
        negation_tuples = getContext(dbi, neg_table)
        mc = miner2.MinerCask(concept_entries, negation_tuples, neg_var)
        all_labels = meta_labels + ['dictid', 'captured', 'context', 'text', 'certainty', 'hypothetical', 'historical',
                                    'otherSubject', '"start"', '"finish"', 'start_idx', 'end_idx']
        all_types = ['varchar(255)'] * len(meta_labels) + ['int', 'varchar(255)', 'varchar(255)', 'varchar(max)', 'int',
                                                           'int', 'int', 'int', 'int', 'int', 'int', 'int']
    else:
        raise ValueError('Invalid version for ConceptMiner: %d.' % concept_miner_v)

    sb = SentenceBoundary(dbi)

    # if batch mode, select all ids, and split into batches
    if batch_mode:
        order_by = ' ORDER BY %s ' % batch_mode
        doc_ids = getDocumentIds(dbi, document_table, batch_mode, order_by)
        # get minimum value of each batch size
        batches = [doc_ids[x * batch_size]
                   for x in range(int(math.ceil(float(len(doc_ids)) / batch_size)))]
    else:
        batches = [None]
        order_by = ''

    # create table
    try:
        createTable(dbi, destination_table, all_labels, all_types)
        logging.info('Table created: %s.' % destination_table)
    except pyodbc.ProgrammingError as pe:
        logging.warning('Table already exists: Using existing table.')
    except Exception as e:
        logging.exception(e)
        logging.error('Failed to create table.')
        raise e

    BATCH_LENGTH = len(batches)
    logging.info('Prepared %d batch(es).' % BATCH_LENGTH)
    for num, batch in enumerate(batches):
        curr_batch = num + 1
        if batch_mode and batch_number and curr_batch not in batch_number:
            continue

        logging.info('Started batch #%d (ending at %d).' % (curr_batch, batch_number[-1] if batch_number else 1))

        if batch_mode:
            where_clause = ' WHERE %s > %d ' % (batch_mode, batch)
        else:
            where_clause = ''
        process(dbi, mc, sb, destination_table, document_table, meta_labels, text_labels, concept_miner_v, all_labels,
                where_clause, order_by, batch_size, max_intervening_terms, max_length_of_search)
        logging.info('Finished batch #%d of %d.' % (num + 1, BATCH_LENGTH))


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

    parser.add_argument('--server', required=False, default='ghrinlp')
    parser.add_argument('--database', required=False, default='nlpdev')
    parser.add_argument('--max-intervening-terms', required=False, default=1, type=int)
    parser.add_argument('--max-length-of-search', required=False, default=3, type=int)
    parser.add_argument('--valence', required=False, default=None, type=int)
    parser.add_argument('--regex-variation', required=False, default=None, type=int)
    parser.add_argument('--word-order', required=False, default=None, type=int)
    args = parser.parse_args()

    term_table = args.term_table  # 'COT_Dict_Clin_Lab_Abuse_09Aug2013'
    neg_table = args.negation_table
    neg_var = args.negation_variation
    document_table = args.document_table  # 'vCOT_Clinabuse_data'
    meta_labels = args.meta_labels  # ['ft_id', 'chsid']
    text_labels = args.text_labels if args.text_labels else [args.text_label]  # 'note_text'
    if not args.text_labels: print 'WARNING: Using deprecated option, --text-label; change to --text-labels.'
    concept_miner_v = args.concept_miner
    destination_table = args.destination_table  # 'COT_LOCAL_Clinabuse_out_20131020'
    batch_mode = args.batch_mode
    batch_size = args.batch_size
    batch_number = args.batch_number

    loglevel = mylogger.resolveVerbosity(args.verbosity)

    if batch_mode and batch_number and len(batch_number) > 1:
        batch_number.sort()
        batch_number = range(batch_number[0], batch_number[-1])

        logging.config.dictConfig(mylogger.setup('ctakes-processor' + str(batch_number[0]), loglevel=loglevel))
    else:
        logging.config.dictConfig(mylogger.setup('ctakes-processor', loglevel=loglevel))

    try:
        prepare(term_table, neg_table, neg_var, document_table, meta_labels, text_labels, concept_miner_v,
                destination_table, batch_mode, batch_size, batch_number, args.server, args.database,
                args.max_intervening_terms, args.max_length_of_search, args.valence, args.regex_variation,
                args.word_order)
    except Exception as e:
        import traceback

        logging.info(traceback.format_exc())
        logging.error(e)
        sys.exit(1)  # this will signal a batch file
    sys.exit(0)
