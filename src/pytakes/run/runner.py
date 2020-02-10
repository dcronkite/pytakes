from datetime import datetime
from typing import List

from pytakes import MinerCollection, SentenceBoundary
from pytakes.corpus import get_next_from_corpus
from pytakes.dict.textitem import process_textitem
from pytakes.run.schema import validate_config
from pytakes.run.simple_run import load_keywords, load_negation, output_context_manager


def run(corpus=None, output=None, keywords: List = None, negation=None, logger=None):
    """

    :return:
    """
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(load_keywords(*keywords))
    mc.add(load_negation(**negation))
    default_output = {
        'outfile': 'extracted_concepts_{}.jsonl'.format(datetime.now().strftime('%Y%m%d_%H%M%S')),
        'metalabels': ['file'],
    }
    with output_context_manager(**{**default_output, **output}) as out:
        for i, ti in enumerate(get_next_from_corpus(**corpus)):
            for results, sent in process_textitem(ti, mc):
                for result in results:
                    out.writerow(result, meta=list(ti.meta.values()), text=sent)


def run_config(config_file):
    run(**validate_config(config_file))
