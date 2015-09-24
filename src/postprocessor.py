'''
This is a fix since currently Lctakes does not deal with concept-internal 
negation like: 'opioids no abuse'; currently, this will resolve to a positive
mention.

'''

import argparse
import copy
import logging
import logging.config
import pyodbc
from itertools import izip

from ghri.db_reader import dbInterface
from ghri import mylogger
from ghri.nlp.negex import myStatusTagger, sortRulesForStatus, getContext
from ghri.utils import get_valid_args


def listsAreEqual(lst1, lst2):
    for el1, el2 in izip(lst1, lst2):
        if el1 != el2:
            return False
    return True
        

def insertInto(dbi, table, cols, row):    
    '''
    
    '''
    sql = u'''
        INSERT INTO %s ( "%s" )
        VALUES (
    ''' % (table, '", "'.join(cols[1:]))
    sql += ', '.join([str(r) if isinstance(r, int) else "'"+r+"'" for r in row[1:]])
    sql += ')'
    
    try:
        dbi.execute_commit(sql)
    except Exception as e:
        logging.error( sql )
        logging.exception( e )
        raise e
    


def getInputData(dbi, input_table, columns):
    sql = '''
        SELECT "%s"
        FROM %s
    ''' % ('", "'.join(columns),
           input_table)
    return dbi.execute_fetchall( sql )


def createDestinationTable(dbi, input_table, output_table):
    '''
    Copy all attributes of input to output table.
    '''
    try:
        dbi.execute_commit('''
            SELECT * INTO %s FROM %s
            WHERE 1 = 2
        ''' % (output_table, input_table))
    except pyodbc.ProgrammingError:
        logging.warning('Table "%s" already exists.' % output_table)
        return
    
    # add new column to show where changes happened
    dbi.execute_commit('''
        ALTER TABLE %s
        ADD updated int
    ''' % output_table)


def addRowid(dbi,
             output_table):
    '''
    Add row id for output column
    '''
    try:
        dbi.execute_commit('''
            ALTER TABLE %s
            ADD rowid bigint IDENTITY(1,1)
        ''' % output_table)
    except pyodbc.ProgrammingError as e:
        logging.error('Failed to create identity column.')
        logging.exception(e)
        # don't raise exception since this is the last call of program
        # also, this is currently untested, so if it fails,
        # I don't want to think something went wrong, just know 
        # that something needs to be fixed. :)


def main(dbi,
         negation_table, 
         negation_variation,
         input_table,
         input_column,
         output_table):
    '''
    
    '''
    tagger = myStatusTagger(sortRulesForStatus(getContext(dbi, negation_table)), rxVar=negation_variation)
    columns = dbi.getTableColumns( input_table )
    if input_column in columns:
        col_idx = columns.index(input_column)
    else:
        raise ValueError('Unrecognized column "%s" in table %s.' % (input_column, input_table))
    data = getInputData(dbi, input_table, columns)
    
    createDestinationTable(dbi, input_table, output_table)
    columns.append('updated')
    for row in data:
        new_row = []
        for el in row:
            if isinstance(el, int):
                new_row.append(el)
            else:
                new_row.append(el.decode('utf-8','ignore'))
        row = new_row
        text = row[col_idx]
        orig_row = copy.copy(row)
        for negConcept in tagger.findNegation(text):
            type = negConcept.type().lower()
            if type == 'negn':
                row[ columns.index('certainty') ] = 0
            elif type == 'impr':
                row[ columns.index('certainty') ] = 1
            elif type == 'poss':
                row[ columns.index('certainty') ] = 2
            elif type == 'prob':
                row[ columns.index('certainty') ] = 3
            if type == 'hypo':
                row[ columns.index('hypothetical') ] = 1
            if type == 'futp':
                row[ columns.index('hypothetical') ] = 1
            if type == 'hist':
                row[ columns.index('historical') ] = 1
            if type == 'othr':
                row[ columns.index('otherSubject') ] = 1
        
        if listsAreEqual(orig_row, row):
            row.append(0)
        else:
            row.append(1)
            
        insertInto(dbi, output_table, columns, row)
        
#     addRowid(dbi, output_table)
    return True
        
    
                
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-s','--server',default='ghrinlp',help='Database server to use.')
    parser.add_argument('-d','--database',default='nlpdev',help='Database to use.')
    parser.add_argument('--negation-table', help='Table of negation triggers, along with role.')
    parser.add_argument('--negation-variation', type=int, default=0, required=False, help='Amount of variation to allow in negations. Values: 0-3.')
    parser.add_argument('--input-table', help='Table that has a column which needs to be evaluated by negex.')
    parser.add_argument('--input-column', help='Column name which needs to be modified.')
    parser.add_argument('--output-table', help='Output table.')
    
    parser.add_argument('--verbosity', type=int, default=2, help='Verbosity of log output.')
    args = parser.parse_args()
    
    loglevel = mylogger.resolveVerbosity( args.verbosity )
    logging.config.dictConfig( mylogger.setup(name='postprocessor', loglevel=loglevel) )
    
    dbi = dbInterface('SQL Server', args.server, args.database, loglevel)

    try:
        main(dbi, **get_valid_args(main, vars(args)))
    except Exception as e:
        logging.exception(e)
        logging.error('Process terminated.')
