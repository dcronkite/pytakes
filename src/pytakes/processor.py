"""

Edit:
2013-12-24    added line-ending splitting
2013-12-05    added begin/end offsets for conceptminer2
2013-11-26    added option for conceptminer2
"""

import argparse
import logging
import logging.config
from typing import List

from pytakes import Document, Dictionary, Output
from pytakes import MinerCollection, ConceptMiner, StatusMiner
from pytakes.parser import parse_processor
from pytakes import SentenceBoundary


def prepare(documents: List[Document], dictionaries: List[Dictionary],
            outputs: List[Output], negation_dicts: List[Dictionary]):
    """
    :param documents:
    :param dictionaries:
    :param outputs:
    :param negation_dicts:
    """
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(ConceptMiner(dictionaries))
    mc.add(StatusMiner(negation_dicts))

    for out in outputs:
        out.create_output()

    logging.info('Retrieving notes.')
    for document in documents:
        for num, doc in enumerate(document.read_next()):
            if num % 100 == 0:
                logging.info(f'Completed: {num:>5}.')

            for sent_no, (sentence, cleaned_text) in enumerate(mc.parse(doc)):
                for feat, new in sentence:
                    for out in outputs:
                        out.writerow(doc.get_metalist(), feat, text=doc.get_text())
    logging.info('Completed: 100%')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--json-config',
                        help='Json file containing configuration information.')
    args = parser.parse_args()
    parse_processor(args.json_config)


if __name__ == '__main__':
    main()
