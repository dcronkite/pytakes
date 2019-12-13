"""
This is a fix since currently Lctakes does not deal with concept-internal
negation like: 'opioids no abuse'; currently, this will resolve to a positive
mention.

"""

import argparse
import copy
import logging
import logging.config
import pyodbc

from jinja2 import Template

from pytakes import templates, header
from .util import mylogger
from .util.utils import get_valid_args

from .nlp.statusminer import MyStatusTagger, sort_rules_for_status, get_context, StatusMiner
from .util.db_reader import DbInterface


def lists_are_equal(lst1, lst2):
    for el1, el2 in zip(lst1, lst2):
        if el1 != el2:
            return False
    return True


def insert_into(dbi, table, cols, row):
    """
    :param dbi:
    :param table:
    :param cols:
    :param row:

    """
    sql = Template(templates.PP_INSERT_INTO).render({
        'table_name': table,
        'labels': cols[1:],
        'values': row[1:]
    })
    try:
        dbi.execute_commit(sql)
    except Exception as e:
        logging.error(sql)
        logging.exception(e)
        raise e


def get_input_data(dbi, input_table, columns):
    sql = Template(templates.PP_INPUT_DATA).render({
        'input_table': input_table,
        'labels': columns
    })
    return dbi.execute_fetchall(sql)


def create_destination_table(dbi, input_table, output_table):
    """
    Copy all attributes of input to output table.
    :param dbi:
    :param input_table:
    :param output_table:
    """
    sql = Template(templates.PP_DEST_TABLE).render({
        'dest_table': output_table,
        'input_table': input_table
    })
    try:
        dbi.execute_commit(sql)
        prepare_output_tables(dbi, output_table)
    except pyodbc.ProgrammingError as pe:
        logging.warning('Table "%s" already exists.' % output_table)
        return


def prepare_output_tables(dbi, output_table):
    """

    :param dbi:
    :param output_table:
    :return:
    """
    sql = Template(templates.PP_PREP_DEST_TABLE).render({
        'table_name': output_table
    })
    dbi.execute_commit(sql)


def postprocess(dbi,
                negation_table,
                negation_variation,
                input_table,
                input_column,
                output_table,
                batch_count,
                tracking_method):
    """
    :param tracking_method:
    :param batch_count:
    :param dbi:
    :param negation_table:
    :param negation_variation:
    :param input_table:
    :param input_column:
    :param output_table:

    """
    tagger = MyStatusTagger(sort_rules_for_status(get_context(dbi, negation_table)), rx_var=negation_variation)

    if tracking_method == 'name':
        first_input_table = '{}_{}'.format(input_table, 1)  # input table for first instance
    elif tracking_method == 'column':
        first_input_table = input_table
    else:
        raise ValueError('Unrecognized tracking method: "{}".'.format(tracking_method))

    columns = dbi.get_table_columns(first_input_table)
    out_columns = list(columns)
    out_columns.append('updated')
    create_destination_table(dbi, first_input_table, output_table)
    if input_column in out_columns:
        col_idx = out_columns.index(input_column)
    else:
        raise ValueError('Unrecognized column "%s" in table %s.' % (input_column, input_table))

    for i in range(1, batch_count):
        if tracking_method == 'name':
            curr_input_table = '{}_{}'.format(input_table, 1)  # input table for first instance
        elif tracking_method == 'column':
            curr_input_table = input_table
        else:
            raise ValueError('Unrecognized tracking method: "{}".'.format(tracking_method))

        data = get_input_data(dbi, curr_input_table, columns)
        for row in data:
            new_row = []
            for el in row:
                if isinstance(el, int):
                    new_row.append(el)
                else:
                    new_row.append(el.encode('utf-8').decode('utf-8', 'ignore'))
            row = new_row
            text = row[col_idx]
            orig_row = copy.copy(row)
            for negConcept in tagger.find_negation(text):
                _type = negConcept.type().lower()
                if _type == header.NEGATION_TYPE:
                    row[out_columns.index(header.CERTAINTY)] = 0
                elif _type == header.IMPROBABLE_TYPE:
                    row[out_columns.index(header.CERTAINTY)] = 1
                elif _type == header.POSSIBLE_TYPE:
                    row[out_columns.index(header.CERTAINTY)] = 2
                elif _type == header.PROBABLE_TYPE:
                    row[out_columns.index(header.CERTAINTY)] = 3
                if _type == header.HYPOTHETICAL_TYPE:
                    row[out_columns.index(header.HYPOTHETICAL)] = 1
                if _type == header.FUTURE_TYPE:
                    row[out_columns.index(header.HYPOTHETICAL)] = 1
                if _type == header.HISTORICAL_TYPE:
                    row[out_columns.index(header.HISTORICAL)] = 1
                if _type == header.OTHER_SUBJECT_TYPE:
                    row[out_columns.index(header.OTHER_SUBJECT)] = 1

            if lists_are_equal(orig_row, row):
                row.append(0)
            else:
                row.append(1)

            insert_into(dbi, output_table, out_columns, row)

    return True


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--driver', required=False, default='SQL Server')
    parser.add_argument('-s', '--server', required=True, help='Database server to use.')
    parser.add_argument('-d', '--database', required=True, help='Database to use.')
    parser.add_argument('--negation-table', help='Table of negation triggers, along with role.')
    parser.add_argument('--negation-variation', type=int, default=0, required=False,
                        help='Amount of variation to allow in negations. Values: 0-3.')
    parser.add_argument('--input-table', help='Table that has a column which needs to be evaluated by negex.')
    parser.add_argument('--input-column', help='Column name which needs to be modified.')
    parser.add_argument('--output-table', help='Output table.')
    parser.add_argument('--batch-count', type=int, help='Batch count.')
    parser.add_argument('--tracking-method', choices=['name', 'column'], default='name',
                        help='Method to track progress of batches.')

    parser.add_argument('--verbosity', type=int, default=2, help='Verbosity of log output.')
    args = parser.parse_args()

    loglevel = mylogger.resolve_verbosity(args.verbosity)
    logging.config.dictConfig(mylogger.setup(name='postprocessor', loglevel=loglevel))

    dbi = DbInterface(args.driver, args.server, args.database, loglevel)

    try:
        postprocess(dbi, **get_valid_args(postprocess, vars(args)))
    except Exception as e:
        logging.exception(e)
        logging.error('Process terminated.')


if __name__ == '__main__':
    main()
