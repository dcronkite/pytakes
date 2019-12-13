"""
Create a negex-styled dictionary from a tab-delimited
negation list, and a negation equivalences file.

"""

import argparse
import copy
import logging
import logging.config
import pyodbc

import regex as re
from .util import mylogger

from pytakes.util.db_reader import DbInterface


def parse_equivalence_file(eqfile, equivs):
    with open(eqfile) as f:
        for line in f.readlines():
            equiv, defn = line.strip().split('=')
            if equiv in equivs:
                equivs[equiv] += defn.split('||')
            else:
                equivs[equiv] = defn.split('||')


def parse_equivalence_files(eqfiles):
    equivs = {}  # { equiv : list(synonym, synonym, etc.) }
    for eqFile in eqfiles:
        parse_equivalence_file(eqFile, equivs)
    return equivs


def write_termlist_to_file(termlist, outfile, columns):
    with open(outfile, 'w') as out:
        out.write('\t'.join(columns) + '\n')
        for result in termlist:
            if len(columns) == 3:
                terms, _type, direction = result
                out.write('\t'.join([terms, _type, direction]) + '\n')
            else:
                raise Exception('This should not happen.')
    return True


def write_termlist_to_db(termlist, dbi, table_name, columns):
    sqltypes = ['varchar(255)', 'varchar(10)', 'int']
    create_query = ','.join([col + ' ' + st for col, st in zip(columns, sqltypes)])
    try:
        dbi.execute_commit('''
            CREATE TABLE %s
            (
                %s
            );
        ''' % (table_name, create_query))
    except pyodbc.ProgrammingError:
        logging.warning('Appending to existing table "%s".' % table_name)

    insert_query = ','.join(columns)
    values_query = None
    try:
        for result in termlist:
            values_query = ','.join([x if c == 'int' else "'" + x + "'" for x, c in zip(result, columns) if c])
            dbi.execute_commit('''
                INSERT INTO %s (%s)
                VALUES (%s)
            ''' % (table_name, insert_query, values_query))
    except Exception as e:
        logging.exception(e)
        logging.error('Unable to insert values: "%s".' % values_query)

    return True


def create_negex(negex_files, eqfiles, output_file=None, dbi=None, table_name='test',
                 instances=('negex', 'type', 'direction')):
    length_of_instances = 0
    equivs = parse_equivalence_files(eqfiles)
    final_termlist = []
    pattern = re.compile('%([A-Z-_]+)%([A-Za-z-_]*)')
    for negexfile in negex_files:
        with open(negexfile) as f:
            for num, line in enumerate(f.readlines()):
                line = line.strip().split('#')[0]
                if not line or line[0] == '#':
                    continue
                lst = line.split('\t')
                length_of_instances = len(lst)
                if len(lst) < 3:
                    logging.warning('Insufficient instances in line %d of %s. Skipping.' % (num, negexfile))
                    logging.debug(lst)
                    continue
                elif len(lst) == 3:
                    term, _type, direction = lst
                else:
                    logging.warning('Only the first three negation configurations are being read (%s).' % negexfile)
                    term, _type, direction = lst[:3]

                results = [([], _type, direction)]  # start with a single empty list
                for tt in term.split():
                    m = pattern.match(tt)
                    if m:
                        new_results = []
                        for termlist, _type, direction in results:
                            synonyms = equivs[m.group(1)]
                            for eq in synonyms:
                                ctermlist = copy.copy(termlist)
                                ctermlist.append(eq + m.group(2))
                                new_results.append((ctermlist, _type, direction))
                        results = new_results
                    else:
                        for termlist, _type, direction in results:
                            termlist.append(tt)
                final_termlist += [(' '.join(x), y, z) for x, y, z in results]

    if output_file:
        write_termlist_to_file(final_termlist, output_file, instances[:length_of_instances])

    if dbi:
        write_termlist_to_db(final_termlist, dbi, table_name, instances[:length_of_instances])


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--negex-files', required=True, nargs='+')
    parser.add_argument('--equiv-files', required=True, nargs='+')
    parser.add_argument('--output-file', required=False, default=False,
                        help='If included, negexes will write to file.')
    parser.add_argument('--output-driver', required=False, default=False,
                        help='Driver for output table to be written.')
    parser.add_argument('--output-server', required=False, default=False,
                        help='Server for output table to be written.')
    parser.add_argument('--output-database', required=False, default=False,
                        help='Database for output table to be written.')
    parser.add_argument('--output-table', required=False, default=False,
                        help='If included negexes will write to table.')

    parser.add_argument('--verbosity', type=int, default=2, help='Verbosity of log output.')
    args = parser.parse_args()

    if args.verbosity <= 0:
        loglevel = logging.ERROR
    elif args.verbosity == 1:
        loglevel = logging.WARNING
    elif args.verbosity == 2:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    logging.config.dictConfig(mylogger.setup(loglevel=loglevel))

    if args.output_table:
        dbi = DbInterface(args.output_driver, args.output_server, args.output_database)
    else:
        dbi = None

    create_negex(args.negex_files, args.equiv_files, args.output_file, dbi, args.output_table)


if __name__ == '__main__':
    main()
