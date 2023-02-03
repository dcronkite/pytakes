"""
Author: David Cronkite, GHRI
Date: 20dec12
Purpose:
    Methods for simplying the creation of a logfile
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup(name=__name__, logdir=Path('log'), console=True, text=True, loglevel='DEBUG', logfile=None):
    """
    function:
        prepares a logger that can print to both the console and a logfile
    parameters:
        name - the logger's name (for the call logging.getLogger(name))
        logdir - location for the output logfile (default is current dir)
        console - print to console
        text - print to logfile
        loglevel - level for logger (logging.DEBUG)
        logfile - name of logfile (default=name + '.log')
    use:
        logging.config.dictConfig( mylogger.setup(name, etc.) )
        :param console:
        :param text:
        :param loglevel:
        :param logfile:
        :param logdir:
        :param name:
    """
    logdir.mkdir(exist_ok=True)
    if not logfile:
        logfile = name + '.log'

    handler_list = []
    if console:
        handler_list.append('console')
    if text:
        handler_list.append('text')

    config_dict = {'version': 1,
                   'disable_existing_loggers': False,
                   'formatters': {
                       'standard': {
                           'format': '%(asctime)s - %(levelname)s: %(message)s',
                       },
                   },
                   'handlers': {
                       'text': {
                           'level': loglevel,
                           'class': 'logging.handlers.RotatingFileHandler',
                           'backupCount': 5,
                           'filename': logdir / logfile,
                           'formatter': 'standard'
                       },
                       'console': {
                           'class': 'logging.StreamHandler',
                           'level': loglevel,
                           'formatter': 'standard',
                           'stream': 'ext://sys.stdout'
                       }
                   },
                   'loggers': {
                       name: {
                           'level': loglevel,
                           'handlers': handler_list
                       }
                   },
                   'root': {
                       'level': loglevel,
                       'handlers': handler_list}

                   }

    return config_dict


def setup_local(name=__name__, logdir=Path('log'), console=True, text=True, loglevel=logging.DEBUG, logfile=None):
    """
        function:
                prepares a logger that can print to both the console and a logfile
        parameters:
                name - the logger's name (for the call logging.getLogger(name))
                logdir - location for the output logfile (default is current dir)
                console - print to console
                text - print to logfile
                loglevel - level for logger (logging.DEBUG)
                logfile - name of logfile (default=name + '.log')
        use:
                mylogger.setup(name, etc.)
                logger = mylogger.getLogger(name)
                :param name:
                :param logdir:
                :param console:
                :param text:
                :param loglevel:
                :param logfile:
        """
    logdir.mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    if not logfile:
        logfile = name + '.log'

    if text:
        txt_handler = RotatingFileHandler(logdir / logfile, backupCount=5)
        txt_handler.doRollover()
        txt_handler.setFormatter(formatter)
        logger.addHandler(txt_handler)

    if console:
        scrn_handler = logging.StreamHandler()
        scrn_handler.setFormatter(formatter)
        logger.addHandler(scrn_handler)

    return logging.getLogger(name)


def get_logger(name=__name__):
    return logging.getLogger(name)


def resolve_verbosity(verbosity_level):
    """
    Resolves verbosity based on the assumption that:
    3=Debug
    2=info
    1=warning
    0=error

    Returns logging.[LOGLEVEL]
    :param verbosity_level:
    """
    if verbosity_level <= 0:
        loglevel = logging.ERROR
    elif verbosity_level == 1:
        loglevel = logging.WARNING
    elif verbosity_level == 2:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG
    return loglevel
