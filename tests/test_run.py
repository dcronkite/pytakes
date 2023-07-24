import tempfile
from pathlib import Path

from pytakes.run.runner import run_config
from pytakes.run.schema import validate_config


def get_outpath(config):
    return Path(config['output']['path']) / config['output']['outfile']


def test_run_config_jsonl():
    path = Path(__file__).absolute().parent
    config_file = path / 'data' / 'config' / 'run.config.py'
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp:
        with open(config_file) as fh:
            data = fh.read().replace('BASE_PATH', str(path))
        temp.write(data)
    config = validate_config(temp.name)
    run_config(temp.name)  # cannot run `run_config` directly, otherwise paths will not line up correctly
    with open(get_outpath(config)) as fh:
        actual = fh.read()
    with open(path / 'data' / 'testout' / 'expected.negex.jsonl') as fh:
        expected = fh.read()
    assert actual == expected


def test_run_is_regex_false_config_jsonl():
    path = Path(__file__).absolute().parent
    config_file = path / 'data' / 'config' / 'run.is_regex_false.config.py'
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp:
        with open(config_file) as fh:
            data = fh.read().replace('BASE_PATH', str(path))
        temp.write(data)
    config = validate_config(temp.name)
    run_config(temp.name)  # cannot run `run_config` directly, otherwise paths will not line up correctly
    with open(get_outpath(config)) as fh:
        actual = fh.read()
    with open(path / 'data' / 'testout' / 'expected.is_regex_false.jsonl') as fh:
        expected = fh.read()
    for i, (actual_line, exp_line) in enumerate(zip(actual.split('\n'), expected.split('\n'))):
        assert actual_line == exp_line, i
    assert actual == expected
