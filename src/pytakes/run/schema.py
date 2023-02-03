import json
from pathlib import Path

import jsonschema

JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'corpus': {
            'type': 'object',
            'properties': {
                'directories': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'directory': {'type': 'string'},
                            'encoding': {'type': 'string'},
                            'include_extension': {'type': 'string'},
                            'exclude_extension': {'type': 'string'},
                        },
                    },
                },
                'connections': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'driver': {'type': 'string'},
                            'server': {'type': 'string'},
                            'database': {'type': 'string'},
                            'name_col': {'type': 'string'},
                            'text_col': {'type': 'string'}
                        }
                    }
                },
            }
        },
        'keywords': {  # paths to keyword files
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                    'regex_variation': {'type': 'integer'},  # -1 to 3
                    'word_order': {'type': 'integer'},
                    'max_search': {'type': 'integer'},
                    'max_intervening': {'type': 'integer'},
                }
            }
        },
        'negation': {
            'type': 'object',
            'properties': {
                'version': {'type': 'integer'},  # built-in version
                'path': {'type': 'string'},
                'skip': {'type': 'boolean'},
                'variation': {'type': 'integer'},
            }
        },
        'output': {
            'type': 'object',
            'properties': {
                'outfile': {'type': 'string'},
                'path': {'type': 'string'},
                'hostname': {'type': 'string'},
            }
        },
        'logger': {
            'type': 'object',
            'properties': {
                'verbose': {'type': 'boolean'}
            }
        }
    }
}


def myexec(code):
    import warnings
    warnings.warn('Executing python external file: only do this if you trust it')
    import sys
    from io import StringIO
    temp_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        # try if this is a expression
        ret = eval(code)
        result = sys.stdout.getvalue()
        if ret:
            result = result + ret
    except:
        try:
            exec(code)
        except:
            # you can use <traceback> module here
            import traceback
            buf = StringIO()
            traceback.print_exc(file=buf)
            error = buf.getvalue()
            raise ValueError(error)
        else:
            result = sys.stdout.getvalue()
    sys.stdout = temp_stdout
    return result


def load_yaml(fh):
    try:
        import yaml  # pyyaml
        return yaml.load(fh, Loader=yaml.Loader)
    except ModuleNotFoundError:
        try:
            from ruamel import yaml
            return yaml.load(fh)
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Missing module: `yaml`. Install pyyaml or ruamel.yaml from pip.')


def get_config(path):
    with open(path) as fh:
        if path.endswith('json'):
            return json.load(fh)
        elif path.endswith('yaml'):
            return load_yaml(fh)
        elif path.endswith('py'):
            return eval(myexec(fh.read()))
        else:
            raise ValueError('Unrecognized configuration file type: {}'.format(path.split('.')[-1]))


def typify_schema(conf):
    if corpus := conf.get('corpus', None):
        if directories := corpus.get('directories', None):
            for directory in directories:
                directory['directory'] = Path(directory['directory'])
    if keywords := conf.get('keywords', None):
        for keyword in keywords:
            keyword['path'] = Path(keyword['path'])
    if output := conf.get('output', None):
        output['path'] = Path(output.get('path', '.'))


def validate_config(path):
    conf = get_config(path)
    jsonschema.validate(conf, JSON_SCHEMA)
    typify_schema(conf)  # make directories pathlib.Paths
    return conf
