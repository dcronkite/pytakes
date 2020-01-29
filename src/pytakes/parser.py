"""

"""
import json

from pytakes.iolib.config import get_data_item
from pytakes import MinerCollection
from pytakes.util.db_reader import DbInterface

DEFAULT_NEGATION_VARIATION = -1


def _parse(dicts, res, conn):
    ds = []
    for name in dicts:
        resource = res[dicts[name]['resource']]
        ds.append(
            get_data_item(
                resource,
                name,
                conn=conn[resource['connection']]
            )
        )
    return ds


def parse_miner(dicts, res, conn):
    miners = MinerCollection()
    for name in dicts:
        c = dicts[name]
        if c['type'] == 'keyword':
            for neg in c.get('negation', list()):
                negvar = neg.get('variation', DEFAULT_NEGATION_VARIATION)
                cxcn = res[c['resource']]
        elif c['type'] == 'ngram':
            pass
        else:
            raise ValueError('Unrecognized miner type: {}'.format(dicts[name]['type']))
    return miners


def parse_processor(json_file):
    config = json.load(json_file)
    res = config['resources']
    conns = config['connections']
    conn = {c: DbInterface(driver=c['driver'],
                           server=c['server'],
                           database=c['database']) for c in conns}
    dicts = _parse(config['dictionary'], res, conn)
    docs = _parse(config['document'], res, conn)
    out = _parse(config['output'], res, conn)
    miners = parse_miner(config['miner'], res, conn)
    return {
        'dictionary': dicts,
        'document': docs,
        'output': out
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--json-config',
                        help='')
    args = parser.parse_args()
    parse_processor(args.json_config)
