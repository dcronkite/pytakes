import json

import jsonschema
try:
    from ruamel import yaml
except ModuleNotFoundError:
    yaml = False

JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'corpus': {
            'type': 'object',
            'properties': {
                'directories': {
                    'type': 'array',
                    'items': {'type': 'string'}
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
        'keywords': {
            'type': 'array',
            'items': {'type': 'string'}  # paths
        },
        'negation': {
            'type': 'object',
            'properties': {
                'version': {'type': 'integer'},  # built-in version
                'path': {'type': 'string'},
                'skip': {'type': 'boolean'}
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


def get_config(path):
    with open(path) as fh:
        if path.endswith('json'):
            return json.load(fh)
        elif path.endswith('yaml') and yaml:
            return yaml.load(fh)
        elif path.endswith('py'):
            return eval(myexec(fh.read()))
        else:
            raise ValueError('Unrecognized configuration file type: {}'.format(path.split('.')[-1]))


def validate_config(path):
    conf = get_config(path)
    jsonschema.validate(conf, JSON_SCHEMA)
    return conf
