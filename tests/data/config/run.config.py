import os

base_path = r'BASE_PATH'

config = {
    'corpus': {  # how to get the text data
        'directories': [  # specify path to .txt files
            os.path.join(base_path, 'data', 'files')
        ],
    },
    'keywords': [  # path to keyword files, usually stored as CSV
        os.path.join(base_path, 'data', 'concepts.csv')
    ],
    'negation': {
        'path': os.path.join(base_path, 'data', 'negation.csv'),
    },
    'output': {
        'path': os.path.join(base_path, 'data', 'testout'),
        'outfile': 'run.negex.jsonl',  # name of output file (or given default name)
        'hostname': 'Eumaeus'
    },
}

print(config)
