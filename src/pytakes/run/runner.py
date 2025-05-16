import sys
from datetime import datetime
from typing import List

from loguru import logger

from pytakes import MinerCollection, SentenceBoundary
from pytakes.corpus import get_next_from_corpus
from pytakes.dict.textitem import process_textitem
from pytakes.run.schema import validate_config
from pytakes.run.simple_run import load_keywords, load_negation, output_context_manager


def run(corpus=None, output=None, keywords: List = None, negation=None, log=None):
    """

    :return:
    """
    if log and log.get('file', None):
        logger.add(log['file'], level=log.get('level', 'DEBUG'))
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(load_keywords(*keywords))
    mc.add(load_negation(**negation))
    default_output = {
        'outfile': 'extracted_concepts_{}.jsonl'.format(datetime.now().strftime('%Y%m%d_%H%M%S')),
        'metalabels': ['file'],
    }
    with output_context_manager(**{**default_output, **output}) as out:
        for i, ti in enumerate(get_next_from_corpus(**corpus), start=1):
            for results, sent in process_textitem(ti, mc):
                for result in results:
                    out.writerow(result, meta=list(ti.meta.values()), text=sent)
            if i % 10000 == 0:
                logger.info(f'Completed processing of {i} records.')


def run_config(config_file):
    run(**validate_config(config_file))


if __name__ == '__main__':
    run_config(sys.argv[1])
