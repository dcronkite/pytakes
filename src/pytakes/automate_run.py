"""
automate_run.py

Author: Cronkite, David

PURPOSE
-----------
Automate creation of a directory to run pyctakes in batches.

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
from pathlib import Path

from jinja2 import Template
from pytakes.util import mylogger
from pytakes.util.utils import get_valid_args

from pytakes import templates
from pytakes.util.db_reader import DbInterface


def get_integer(s):
    num = None
    while True:
        num = input(s)
        try:
            num = int(num)
            break
        except ValueError as e:
            print("Not a valid number.")
    return num


def is_this_okay():
    response = input('Is this okay? ')
    return 'y' in response.lower()


def get_batch_size(count):
    while True:
        batchsize = get_integer('Size of batches: ')
        batches = int(math.ceil(float(count) / batchsize))
        print("This will result in %d batches." % batches)
        if is_this_okay():
            return batchsize, batches


def get_number_of_files(batches):
    while True:
        filecount = get_integer('Number of batch files: ')
        filebatchcount = int(math.ceil(float(batches) / filecount))
        print('This will result in %d batches per file.' % filebatchcount)
        if is_this_okay():
            return filecount, filebatchcount


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


def create_batch_file(output_dir, batch_label, document_table, destination_table,
                      batch_size, batch_start, batch_end, driver, server, database,
                      meta_labels, primary_key, text_labels,
                      options, python, pytakes_path, tracking_method, send_email):
    with open(output_dir / f'pytakes-batch{batch_label}.bat', 'w') as out:
        if pytakes_path:
            out.write(Template(templates.RUN_BATCH_FILE).render(
                batch_number=batch_label, python=python, pytakes_path=pytakes_path, send_email=send_email))
        else:
            out.write(Template(templates.RUN_COMMAND_BATCH_FILE).render(
                batch_number=batch_label, send_email=send_email
            ))

    if primary_key in meta_labels:
        meta_labels.remove(primary_key)

    with open(output_dir / 'pytakes-batch{batch_label}.conf', 'w') as out:
        out.write(
            Template(templates.RUN_CONF_FILE).render(
                driver=driver, server=server, database=database, document_table=document_table,
                destination_table=destination_table,
                meta_labels=meta_labels, primary_key=primary_key, text_labels=text_labels,
                options=options,
                batch_size=batch_size, batch_start=batch_start, batch_end=batch_end,
                tracking_method=tracking_method
            ))


def create_email_file(output_dir, filecount, destination_table,
                      recipients, sender, mail_server_address, python, pytakes_path):
    with open(output_dir / 'email.conf', 'w') as out:
        out.write(
            Template(templates.EMAIL_CONF_FILE).render(
                recipients=recipients, filecount=filecount, destination_table=destination_table,
                sender=sender, mail_server_address=mail_server_address
            ))

    with open(output_dir / 'bad_email.conf', 'w') as out:
        out.write(
            Template(templates.BAD_EMAIL_CONF_FILE).render(
                recipients=recipients, filecount=filecount, destination_table=destination_table,
                sender=sender, mail_server_address=mail_server_address
            ))


def create_post_process_batch(pp_dir, destination_table, negation_table, negation_variation, driver,
                              server, database, batch_count, python, pytakes_path,
                              tracking_method, send_email):
    with open(pp_dir / 'postprocess.bat', 'w') as out:
        if pytakes_path:
            out.write(Template(templates.PP_BATCH_FILE).render(
                pytakes_path=pytakes_path, python=python
            ))
        else:
            out.write(templates.PP_COMMAND_BATCH_FILE)
    with open(pp_dir / 'postprocess.conf', 'w') as out:
        out.write(Template(templates.PP_CONF_FILE).render(
            driver=driver, server=server, database=database,
            destination_table=destination_table, negation_table=negation_table,
            negation_variation=negation_variation, batch_count=batch_count,
            python=python, pytakes_path=pytakes_path, tracking_method=tracking_method))


def automate_run(dbi, cm_options, concept_miner, document_table,
                 output_dir: Path, destination_table,
                 driver, server, database,
                 meta_labels, primary_key, text_labels,
                 recipients, sender, mail_server_address, negation_table, negation_variation,
                 python, pytakes_path,
                 tracking_method):
    count = dbi.fetch_rowcount(document_table)
    logging.info('Found %d documents in %s.' % (count, document_table))
    batchsize, batchcount = get_batch_size(count)
    filecount, batchesperfile = get_number_of_files(batchcount)

    logging.info('Number of batches: %d' % batchcount)
    logging.info('Batch size: %d' % batchsize)
    logging.info('Number of files: %d' % filecount)
    logging.info('Batches per file: %d' % batchesperfile)

    options = [resolve_formatting(x, y) for x, y in cm_options if y]
    if not primary_key:
        primary_key = meta_labels[0]
    elif primary_key in meta_labels:
        meta_labels.remove(primary_key)

    send_email = recipients and sender and mail_server_address
    output_dir.mkdir(exist_ok=True)
    if send_email:
        create_email_file(output_dir, filecount, destination_table,
                          recipients, sender, mail_server_address, python, pytakes_path)
    else:
        logging.warning(
            'Skipping email: Failed to specify at least one of "recipients", "sender", and "mail server address".')

    postprocess_dir = output_dir / 'post'

    batch_start = 1
    for batch_label in range(1, filecount + 1):
        batch_end = batch_start + batchesperfile
        create_batch_file(output_dir, batch_label, document_table, destination_table,
                          batchsize, batch_start, batch_end, driver, server, database,
                          meta_labels, primary_key, text_labels,
                          options, python, pytakes_path, tracking_method, send_email)
        batch_start = batch_end

    if concept_miner == 2:
        postprocess_dir.mkdir(exist_ok=True)
        create_post_process_batch(postprocess_dir, destination_table, negation_table, negation_variation,
                                  driver, server, database, filecount + 1, python, pytakes_path,
                                  tracking_method, send_email)
    logging.info('Completed.')


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--driver', default='SQL Server', help='Driver to connect with.')
    parser.add_argument('-s', '--server', required=True, help='Database server to use.')
    parser.add_argument('-d', '--database', required=True, help='Database to use.')
    parser.add_argument('--document-table', help='Table of input documents.')
    parser.add_argument('--output-dir', type=Path,
                        help='Destination directory.')
    parser.add_argument('--destination-table', help='Output table, to be created.')

    parser.add_argument('--concept-miner', default=2, type=int, required=False,
                        help='Version of concept miner to use.')
    # concept miner 2
    parser.add_argument('--max-intervening-terms', default=1, type=int,
                        help='Max number of terms that can occur between searched for terms.')
    parser.add_argument('--max-length-of-search', required=False, default=3, type=int,
                        help='Max number of words in which to look for the next term.')
    parser.add_argument('--valence', required=False, default=None, type=int)
    parser.add_argument('--regex-variation', required=False, default=-1, type=int)
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

    parser.add_argument('--meta-labels', required=True, nargs='+',
                        help='Identifying labels to include in output.')
    parser.add_argument('--primary-key', required=False, default=None,
                        help='Primary key for documents. This will be used in sorting batches. '
                             'If not included, the first meta label will be the primary key.')
    parser.add_argument('--text-labels', nargs='+', help='Name of text columns.')

    parser.add_argument('--tracking-method', choices=['name', 'column'], default='name',
                        help='Method to track progress of batches.')

    # library -- these are more for debugging
    parser.add_argument('--python', default='python', help='Specify Python version.')
    parser.add_argument('--pytakes-path', default='',
                        help='Path to pytakes directory, which should contain the "src" directory.'
                             ' Default assumes that you have installed this file in scripts.')

    parser.add_argument('-v', '--verbosity', type=int, default=2, help='Verbosity of log output.')

    # email
    parser.add_argument('--recipients', required=False, default=[], nargs='+',
                        help='In format of "name,email@address"')
    parser.add_argument('--sender', required=False, default=None,
                        help='In format of "name,email@address"')
    parser.add_argument('--mail-server-address', required=False,
                        help='Mail server address.')

    # autogenerate sample config file
    cparser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    cparser.add_argument('--create-sample', action='store_true', default=False,
                         help='Generate a sample configuration file to fill out.')

    args, _ = cparser.parse_known_args()
    if args.create_sample:
        with open('sample_config.conf', 'w') as out:
            out.write(templates.SAMPLE_CONF_FILE)
        return

    args = parser.parse_args()

    loglevel = mylogger.resolve_verbosity(args.verbosity)
    logging.config.dictConfig(mylogger.setup(name='automate_run', loglevel=loglevel))

    dbi = DbInterface(driver=args.driver, server=args.server, database=args.database, loglevel=loglevel)

    if args.concept_miner == 2:
        cm_options = [
            ('concept-miner', 2),
            ('term-table', args.dictionary_table),
            ('max-intervening-terms', args.max_intervening_terms),
            ('max-length-of-search', args.max_length_of_search),
            ('valence', args.valence),
            ('regex-variation', args.regex_variation),
            ('word-order', args.word_order),
            ('destination-table', '{}_pre'.format(args.destination_table))
        ]
        if args.negation_table:
            cm_options += [('negation-table', args.negation_table),
                           ('negation-variation', args.negation_variation)]

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

    # clean recipients (see PYT-15)
    args.recipients = [x for x in args.recipients if x and '@' in x]

    try:
        automate_run(dbi, cm_options, **get_valid_args(automate_run, vars(args)))
    except Exception as e:
        logging.exception(e)
        logging.error('Process terminated with errors.')
    logging.info('Process completed.')


if __name__ == '__main__':
    main()
