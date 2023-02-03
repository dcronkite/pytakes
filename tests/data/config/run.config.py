from pathlib import Path

base_path = Path(r'BASE_PATH')

config = {
    'corpus': {  # how to get the text data
        'directories': [  # specify path to .txt files
            {
                'directory': str(base_path / 'data' / 'files'),
                'encoding': 'utf8',  # optional
                'include_extension': '.txt',  # optional
                'exclude_extension': '.meta',  # optional
            },
        ],
    },
    'keywords': [  # path to keyword files, usually stored as CSV
        {
            'path': str(base_path / 'data' / 'concepts.csv')
        }
    ],
    'negation': {
        # negation defaults to internal data
        'path': str(base_path / 'data' / 'negation.csv'),
    },
    'output': {
        'path': str(base_path / 'data' / 'testout'),
        'outfile': 'run.negex.jsonl',  # name of output file (or given default name)
        'hostname': 'Eumaeus'
    },
}

print(config)
