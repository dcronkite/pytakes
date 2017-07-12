"""

TODO: Make into sql_alchemy.
"""

import pyodbc
import time
import logging


def connection_continue(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except pyodbc.Error as e:
                args[0].wait_for_connection_resume(60, e)
    return wrapper


class DbInterface(object):
    def __init__(self, driver='', server='', database='', loglevel=None):
        """
        open connection
        connection will be closed when it falls out of scope

        Parameters
        -----------
        database - specify database to connect to
        loglevel - deprecated; no longer has any effect
        """
        self._cs = 'DRIVER={%s};SERVER=%s;DATABASE=%s;' % (driver, server, database)
        self.conn = pyodbc.connect(self._cs)
        self.cur = self.conn.cursor()
        # default loglevel is 30 (i.e., logger.WARNING)
        self.logger = logging.getLogger(__name__)
        if loglevel:
            self.logger.setLevel(loglevel)

    def close(self):
        self.__del__()

    def __del__(self):
        """close connection when garbage collecting"""
        try:
            self.conn.close()
        except AttributeError:
            pass

    @connection_continue
    def __next__(self):
        return next(self.cur)

    @connection_continue
    def __iter__(self):
        return self

    @connection_continue
    def fetchall(self):
        return self.cur.fetchall()

    @connection_continue
    def fetchmany(self):
        return self.cur.fetchmany()

    @connection_continue
    def fetchone(self):
        return self.cur.fetchone()

    @connection_continue
    def execute(self, text, debug=False):
        if debug:
            print(text)
        logging.debug(text)
        self.cur.execute(text)

    @connection_continue
    def commit(self):
        self.conn.commit()

    @connection_continue
    def execute_commit(self, text, debug=False):
        self.execute(text, debug)
        self.commit()

    @connection_continue
    def execute_return(self, text, debug=False):
        return self.execute_fetchall(text, debug)

    @connection_continue
    def execute_fetchone(self, text, debug=False):
        self.execute(text, debug)
        return self.fetchone()

    @connection_continue
    def execute_fetchmany(self, text, debug=False):
        self.execute(text, debug)
        return self.fetchmany()

    @connection_continue
    def execute_fetchall(self, text, debug=False):
        self.execute(text, debug)
        return self.fetchall()

    @connection_continue
    def fetch_rowcount(self, table, debug=False):
        sql = '''SELECT COUNT(*) FROM {}'''.format(table)
        return self.execute_fetchone(sql, debug)[0]

    def get_table_columns(self, table_name):
        """returns columns of specified table """
        if self.is_sql_server_connection():
            cols = self.execute_fetchall('''
                SELECT column_name
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE table_name = '%s'
            ''' % table_name)
            return (x[0] for x in cols)
        else:
            raise ValueError('Unsupported database connection.')

    def is_sql_server_connection(self):
        return 'sql server' in self._cs.lower()

    # noinspection PyUnboundLocalVariable
    def wait_for_connection_resume(self, waittime, err):
        while True:
            if isinstance(err, pyodbc.ProgrammingError):
                if err.args[0] == '42000' and '(6005)' in err.args[1]:
                    logging.warning(err)
                else:
                    raise err
            elif isinstance(err, pyodbc.OperationalError):
                if err.args[0] == 'HYT00' and '(0)' in err.args[1]:
                    logging.warning(err)
                else:
                    raise err
            else:  # isinstance(err, pyodbc.Error):
                if err.args[0] == '08001' and '(17)' in err.args[1]:
                    logging.warning(err)
                elif err.args[0] == '01000' and 'General network error' in err.args[1]:
                    logging.warning(err)
                elif err.args[0] == '42000' and '(4060)' in err.args[1]:
                    logging.warning(err)
                else:
                    raise err
            logging.info('Waiting for connection resume.')
            time.sleep(waittime)
            try:
                self.conn = pyodbc.connect(self._cs)
                self.cur = self.conn.cursor()
                break
            except pyodbc.Error as err:
                continue


def parse_dbargs(args):
    import argparse

    db_parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

    db_parser.add_argument('--password', metavar='pwd', required=True, help='SQL Server password.')
    db_parser.add_argument('--user', metavar='u', default=None, help='SQL Server username.')
    db_args, _ = db_parser.parse_known_args(args)
    return db_args
