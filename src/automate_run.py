"""
automate_run.py

Author: Cronkite, David

PURPOSE
-----------
Automate creation of a directory to run Lctakes in batches.

TODO
-------


CHANGELOG
---------------
2013-12-12        created

"""

import argparse
import logging
import logging.config
import math
import os

from ghri.db_reader import dbInterface
from ghri import mylogger
from ghri.unix import mkdir_p
from ghri.utils import get_valid_args


def get_document_count(dbi, table):
    sql = '''
        SELECT COUNT(*)
        FROM %s
    ''' % table
    return dbi.execute_fetchone(sql)[0]


def get_integer(s):
    num = None
    while True:
        num = raw_input(s)
        try:
            num = int(num)
            break
        except ValueError as e:
            print "Not a valid number."
    return num


def is_this_okay():
    response = raw_input('Is this okay? ')
    return 'y' in response.lower()


def get_batch_size(count):
    while True:
        batchSize = get_integer('Size of batches: ')
        batches = int(math.ceil(float(count) / batchSize))
        print "This will result in %d batches." % batches
        if is_this_okay():
            return batchSize, batches


def get_number_of_files(batches):
    while True:
        numberOfFiles = get_integer('Number of batch files: ')
        batchesPerFile = int(math.ceil(float(batches) / numberOfFiles))
        print 'This will result in %d batches per file.' % batchesPerFile
        if is_this_okay():
            return numberOfFiles, batchesPerFile


def resolve_formatting(label, value):
    if value:
        if isinstance(value, bool):
            return '--{}'.format(label)
        elif isinstance(value, list):
            return '--{}\n{}'.format(label, '\n'.join(value))
        else:
            return '--{}={}'.format(label, value)
    else:
        return ''


def create_batch_file(output_dir, number, document_table, destination_table,
                      batch_size, batch_start, batch_end, driver, server, database, meta_labels, cm_options):
    meta_labels = '\n'.join(meta_labels) if meta_labels else '\n'.join(('ft_id', 'chsid'))
    with open(os.path.join(output_dir, 'ctakes-batch' + str(number) + '.bat'), 'w') as out:
        out.write(
            r'''@echo off
echo Running batch %d.
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\processor.py "@.\ctakes-batch%d.conf"
if %%errorlevel%% equ 0 (
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\ghri\email_utils.py -s "Batch %d Completed" "@.\email.conf"
echo Successful.
) else (
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\ghri\email_utils.py -s "Batch %d Failed: Log Included" -f ".\log\ctakes-processor%d.log" "@.\bad_email.conf"
echo Failed.
)
pause''' % (number, number, number, number, batch_start))

    options = '\n'.join(resolve_formatting(x, y) for x, y in cm_options if y)

    with open(os.path.join(output_dir, 'ctakes-batch' + str(number) + '.conf'), 'w') as out:
        out.write(
            r'''--driver={}
--server={}
--database={}
--document-table={}
--meta-labels
{}
--text-labels=note_text
--destination-table={}_pre
{}
--batch-mode=ft_id
--batch-size={}
--batch-number
{}
{}'''.format(driver, server, database, document_table, meta_labels, destination_table,
             options, batch_size, batch_start, batch_end))
    return


def create_email_file(output_dir, numberOfFiles, destination_table, recipients):
    email = '\n'.join(list('\n'.join(['--recipients', rec]) for rec in recipients))
    with open(os.path.join(output_dir, 'email.conf'), 'w') as out:
        out.write(
            r'''%s
--text
This notification is to inform you that another batch (%d total) has been completed for table %s.
''' % (email, numberOfFiles, destination_table))

    with open(os.path.join(output_dir, 'bad_email.conf'), 'w') as out:
        out.write(
            r'''--recipients
%s
--text
This notification is to inform you that a batch (%d total) has failed for table %s.

The log file is included for debugging.
''' % (email, numberOfFiles, destination_table))


def create_post_process_batch(pp_dir, destination_table, negation_table, negation_variation, driver,
                              server, database):
    with open(os.path.join(pp_dir, 'postprocess.bat'), 'w') as out:
        out.write(
            r'''python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\postprocessor.py "@.\postprocess.conf"
pause
''')
    with open(os.path.join(pp_dir, 'postprocess.conf'), 'w') as out:
        out.write(
            r'''--driver=%s
--server=%s
--database=%s
--input-table=%s_pre
--output-table=%s
--negation-table=%s
--negation-variation=%s
--input-column=captured
''' % (driver, server, database, destination_table, destination_table, negation_table, negation_variation))


def main(dbi,
         cm_options,
         concept_miner,
         document_table,
         output_dir,
         destination_table,
         driver,
         server,
         database,
         meta_labels,
         recipients,
         negation_table, negation_variation):
    count = get_document_count(dbi, document_table)
    print 'Found %d documents in %s.' % (count, document_table)
    batchSize, batchCount = get_batch_size(count)
    numberOfFiles, batchesPerFile = get_number_of_files(batchCount)

    logging.info('Number of batches: %d' % batchCount)
    logging.info('Batch size: %d' % batchSize)
    logging.info('Number of files: %d' % numberOfFiles)
    logging.info('Batches per file: %d' % batchesPerFile)

    mkdir_p(output_dir)
    batch_start = 1
    for i in range(1, numberOfFiles + 1):
        batch_end = batch_start + batchesPerFile
        create_batch_file(output_dir, i, document_table, destination_table,
                          batchSize, batch_start, batch_end, driver, server, database, meta_labels,
                          cm_options)
        batch_start = batch_end

    create_email_file(output_dir, numberOfFiles, destination_table, recipients)

    postprocess_dir = os.path.join(output_dir, 'post')

    if concept_miner == 2:
        mkdir_p(postprocess_dir)
        create_post_process_batch(postprocess_dir, destination_table, negation_table, negation_variation,
                                  driver, server, database)
    logging.info('Completed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--driver', default='SQL Server', help='Driver to connect with.')
    parser.add_argument('-s', '--server', default='ghrinlp', help='Database server to use.')
    parser.add_argument('-d', '--database', default='nlpdev', help='Database to use.')
    parser.add_argument('--document-table', help='Table of input documents.')
    parser.add_argument('--output-dir', help='Destination directory.')
    parser.add_argument('--destination-table', help='Output table, to be created.')

    parser.add_argument('--concept-miner', default=2, type=int, required=False,
                        help='Version of concept miner to use.')
    # concept miner 2
    parser.add_argument('--max-intervening-terms', default=1, type=int,
                        help='Max number of terms that can occur between searched for terms.')
    parser.add_argument('--max-length-of-search', required=False, default=3, type=int,
                        help='Max number of words in which to look for the next term.')
    parser.add_argument('--valence', required=False, default=None, type=int)
    parser.add_argument('--regex-variation', required=False, default=None, type=int)
    parser.add_argument('--word-order', required=False, default=None, type=int)
    parser.add_argument('--dictionary-table', help='Term table/dictionary table as input.')
    parser.add_argument('--negation-table', help='Negation/status table with (negex,status,direction).')
    parser.add_argument('--negation-variation', help='Negation variation [0-3].')

    # concept miner 3
    parser.add_argument('--stopwords', required=False, default=None, nargs='+',
                        help='Stopwords to include.')
    parser.add_argument('--number-normalization', required=False, action='store_true', default=False,
                        help='Whether or not to normalize all numbers to a default value.')
    parser.add_argument('--stopword-tables', required=False, default=None, nargs='+',
                        help='Tables containing relevant stopwords. NYI')

    parser.add_argument('--meta-labels', nargs='+', help='Extra identifying labels to include in output.')

    parser.add_argument('-v', '--verbosity', type=int, default=2, help='Verbosity of log output.')
    parser.add_argument('--recipients', required=True, default=None, nargs='+',
                        help='In format of "name,email@address"')
    args = parser.parse_args()

    loglevel = mylogger.resolveVerbosity(args.verbosity)
    logging.config.dictConfig(mylogger.setup(name='automate_run', loglevel=loglevel))

    dbi = dbInterface(driver=args.driver, server=args.server, database=args.database, loglevel=loglevel)

    if args.concept_miner == 2:
        cm_options = [
            ('concept-miner', 2),
            ('term-table', args.dictionary_table),
            ('negation-table', args.negation_table),
            ('negation-variation', args.negation_variation),
            ('max-intervening-terms', args.max_intervening_terms),
            ('max-length-of-search', args.max_length_of_search),
            ('valence', args.valence),
            ('regex-variation', args.regex_variation),
            ('word-order', args.word_order),
            ('destination-table', '{}_pre'.format(args.destination_table))
        ]
    elif args.concept_miner == 3:
        cm_options = [
            ('concept-miner', 3),
            ('stopwords', args.stopwords),
            ('number-normalization', args.number_normalization),
            ('stopword-tables', args.stopword_tables),
            ('destination-table', args.destination_table)
        ]
    else:
        raise ValueError('Invalid argument for concept miner.')

    try:
        main(dbi, cm_options, **get_valid_args(main, vars(args)))
    except Exception as e:
        logging.exception(e)
        logging.error('Process terminated with errors.')
    logging.info('Process completed.')
