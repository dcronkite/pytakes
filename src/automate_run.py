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


def getDocumentCount(dbi, table):
    sql = '''
        SELECT COUNT(*)
        FROM %s
    ''' % table
    return dbi.execute_fetchone(sql)[0]


def getInteger(s):
    num = None
    while True:
        num = raw_input(s)
        try:
            num = int(num)
            break
        except ValueError as e:
            print "Not a valid number."
    return num


def isThisOkay():
    response = raw_input('Is this okay? ')
    return 'y' in response.lower()


def getSizeOfBatches(count):
    while True:
        batchSize = getInteger('Size of batches: ')
        batches = int(math.ceil(float(count) / batchSize))
        print "This will result in %d batches." % batches
        if isThisOkay():
            return batchSize, batches


def getNumberOfFiles(batches):
    while True:
        numberOfFiles = getInteger('Number of batch files: ')
        batchesPerFile = int(math.ceil(float(batches) / numberOfFiles))
        print 'This will result in %d batches per file.' % batchesPerFile
        if isThisOkay():
            return numberOfFiles, batchesPerFile


def createBatchFile(output_dir, number, dictionary_table, negation_table,
                    negation_variation, document_table, destination_table,
                    batch_size, batch_start, batch_end, server, database,
                    max_intervening_terms, max_length_of_search,
                    valence, regex_variation, word_order, meta_labels):
    optional = '\n'.join(['{}={}'.format(x, y) for x, y in [('--valence', valence),
                                                            ('--regex-variation', regex_variation),
                                                            ('--word-order', word_order)]
                          if y])
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

    with open(os.path.join(output_dir, 'ctakes-batch' + str(number) + '.conf'), 'w') as out:
        out.write(
            r'''--server=%s
--database=%s
--term-table=%s
--negation-table=%s
--negation-variation=%s
--document-table=%s
--meta-labels
%s
--text-labels=note_text
--destination-table=%s_pre
--concept-miner=2
--max-intervening-terms=%d
--max-length-of-search=%d
%s
--batch-mode=ft_id
--batch-size=%d
--batch-number
%d
%d''' % (server, database, dictionary_table, negation_table, negation_variation, document_table, meta_labels,
         destination_table, max_intervening_terms, max_length_of_search, optional, batch_size, batch_start, batch_end))
    return


def createEmailFile(output_dir, numberOfFiles, destination_table, recipients):
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
David Cronkite,cronkite.d@ghc.org
--text
This notification is to inform you that a batch (%d total) has failed for table %s.

The log file is included for debugging.
''' % (numberOfFiles, destination_table))


def createPostProcessBatch(pp_dir, destination_table, negation_table, negation_variation,
                           server, database):
    with open(os.path.join(pp_dir, 'postprocess.bat'), 'w') as out:
        out.write(
            r'''python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\postprocessor.py "@.\postprocess.conf"
pause
''')
    with open(os.path.join(pp_dir, 'postprocess.conf'), 'w') as out:
        out.write(
            r'''--server=%s
--database=%s
--input-table=%s_pre
--output-table=%s
--negation-table=%s
--negation-variation=%s
--input-column=captured
''' % (server, database, destination_table, destination_table, negation_table, negation_variation))


def main(dbi,
         dictionary_table,
         negation_table,
         negation_variation,
         document_table,
         output_dir,
         destination_table,
         server,
         database,
         max_intervening_terms,
         max_length_of_search,
         valence,
         regex_variation,
         word_order,
         meta_labels,
         recipients):
    count = getDocumentCount(dbi, document_table)
    print 'Found %d documents in %s.' % (count, document_table)
    batchSize, batchCount = getSizeOfBatches(count)
    numberOfFiles, batchesPerFile = getNumberOfFiles(batchCount)

    logging.info('Number of batches: %d' % batchCount)
    logging.info('Batch size: %d' % batchSize)
    logging.info('Number of files: %d' % numberOfFiles)
    logging.info('Batches per file: %d' % batchesPerFile)

    mkdir_p(output_dir)
    batch_start = 1
    for i in range(1, numberOfFiles + 1):
        batch_end = batch_start + batchesPerFile
        createBatchFile(output_dir, i, dictionary_table, negation_table,
                        negation_variation, document_table, destination_table,
                        batchSize, batch_start, batch_end, server, database, max_intervening_terms,
                        max_length_of_search, valence, regex_variation, word_order, meta_labels)
        batch_start = batch_end

    createEmailFile(output_dir, numberOfFiles, destination_table, recipients)

    postprocess_dir = os.path.join(output_dir, 'post')
    mkdir_p(postprocess_dir)
    createPostProcessBatch(postprocess_dir, destination_table, negation_table, negation_variation,
                           server, database)
    logging.info('Completed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-s', '--server', default='ghrinlp', help='Database server to use.')
    parser.add_argument('-d', '--database', default='nlpdev', help='Database to use.')
    parser.add_argument('--dictionary-table', help='Term table/dictionary table as input.')
    parser.add_argument('--negation-table', help='Negation/status table with (negex,status,direction).')
    parser.add_argument('--negation-variation', help='Negation variation [0-3].')
    parser.add_argument('--document-table', help='Table of input documents.')
    parser.add_argument('--output-dir', help='Destination directory.')
    parser.add_argument('--destination-table', help='Output table, to be created.')
    parser.add_argument('--max-intervening-terms', default=1, type=int,
                        help='Max number of terms that can occur between searched for terms.')
    parser.add_argument('--max-length-of-search', required=False, default=3, type=int,
                        help='Max number of words in which to look for the next term.')

    parser.add_argument('--valence', required=False, default=None, type=int)
    parser.add_argument('--meta-labels', nargs='+', help='Extra identifying labels to include in output.')
    parser.add_argument('--regex-variation', required=False, default=None, type=int)
    parser.add_argument('--word-order', required=False, default=None, type=int)
    parser.add_argument('-v', '--verbosity', type=int, default=2, help='Verbosity of log output.')
    parser.add_argument('--recipients', required=True, default=None, nargs='+',
                                      help='In format of "name,email@address"')
    args = parser.parse_args()

    loglevel = mylogger.resolveVerbosity(args.verbosity)
    logging.config.dictConfig(mylogger.setup(name='automate_run', loglevel=loglevel))

    dbi = dbInterface(driver='SQL Server', server=args.server, database=args.database, loglevel=loglevel)

    try:
        main(dbi, **get_valid_args(main, vars(args)))
    except Exception as e:
        logging.exception(e)
        logging.error('Process terminated with errors.')
    logging.info('Process completed.')
