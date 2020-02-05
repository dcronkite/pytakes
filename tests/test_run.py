import os
import tempfile

from pytakes.run.runner import run_config
from pytakes.run.schema import validate_config


def get_outpath(config):
    return os.path.join(config['output']['path'], config['output']['outfile'])


def test_run_config_jsonl():
    path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(path, 'data', 'config', 'run.config.py')
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp:
        with open(config_file) as fh:
            data = fh.read().replace('BASE_PATH', path)
        temp.write(data)
    config = validate_config(temp.name)
    run_config(temp.name)  # cannot run `run_config` directly, otherwise paths will not line up correctly
    with open(get_outpath(config)) as fh:
        actual = fh.read()
    with open(os.path.join(path, 'data', 'testout', 'expected.negex.jsonl')) as fh:
        expected = fh.read()
    assert actual == expected
