config = {
    'corpus': {  # how to get the text data
        'directories': [  # specify path to .txt files
            r'PATH'
        ],
        'connections': [  # specify other connection types
            {
                'name': 'TABLENAME',
                'name_col': 'TEXT ID COLUMN',
                'text_col': 'TEXT COLUMN',
                # specify either driver/server/database OR connection_string
                # connection string examples here: https://docs.sqlalchemy.org/en/13/core/engines.html
                'connection_string': 'SQLALCHEMY-LIKE CONNECTION_STRING',
                # db args: driver/server/database
                'driver': 'DRIVER',  # available listed in pytakes/iolib/sqlai.py, or use connection string
                'server': 'SERVER',
                'database': 'DATABASE',
            }
        ]
    },
    'keywords': [  # path to keyword files, usually stored as CSV
        {
            'path': r'PATH',
            'regex_variation': 0  # set to -1 if you don't want any expansion
        }
    ],
    'negation': {  # select either version or path (not both)
        'path': r'PATH TO NEGATION CSV FILE',
        'version': 1,  # int (version number), built-in/default
        'skip': False,  # bool: if skip is True: don't do negation
    },
    'output': {
        'path': r'PATH TO OUTPUT DIRECTORY',
        'outfile': 'NAME.out.jsonl',  # name of output file (or given default name)
        'hostname': ''
    },
}

print(config)
