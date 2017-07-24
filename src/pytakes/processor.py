"""

Edit:
2013-12-24    added line-ending splitting
2013-12-05    added begin/end offsets for conceptminer2
2013-11-26    added option for conceptminer2
"""

import argparse
import logging
import logging.config
import pyodbc
import sys
from socket import gethostname
from typing import List

from jinja2 import Template

from pytakes import templates
from pytakes.io.base import Document, Dictionary, Output
from pytakes.parser import parse_processor
from pytakes.util.utils import flatten
from .util import mylogger
from .nlp.ngrams import FeatureMiner
from .nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp import conceptminer2 as miner2


class TextItem(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, meta_list, text):
        self.meta_ = meta_list
        if isinstance(text, str):
            text = [text]
        else:
            text = [t for t in text if t]
        try:
            self.text_ = self.fix_text(text[0])
        except IndexError as e:
            self.text_ = ""
        for txt in text[1:]:
            self.add_text(txt)  # split added 20131224

    def add_text(self, text):
        self.text_ += '\n' + self.fix_text(text)

    def get_text(self):
        return self.text_

    def get_metalist(self):
        return self.meta_

    def fix_text(self, text):
        text = ' '.join(text.split('\n'))
        text.replace('don?t', "don't")  # otherwise the '?' will start a new sentence
        return text


def process(documents: List[Document], outputs: List[Output], mc, sb):
    """
    :param outputs:
    :param documents:
    :param mc:
    :param sb:

    """
    logging.info('Retrieving notes.')
    documents = (doc.read() for doc in documents)

    for document in documents:
        for num, doc in enumerate(document.read_next()):
            if num % 100 == 0:
                logging.info('Completed: {:>5}.'.format(num))

            sentences = []
            for section in sb.ssplit(doc.get_text()):
                sentences += section.split('\n')

            for sect_num, sect in enumerate(mc.mine(sentences)):
                if not sect:
                    continue
                for feat in sect:
                    for out in outputs:
                        out.writerow(doc.get_metalist(), feat, text=doc.get_text())
    logging.info('Completed: 100%')


def prepare(documents: List[Document], dictionaries: List[Dictionary],
            outputs: List[Output], negation_dicts: List[Dictionary]):
    """
    :param documents:
    :param dictionaries:
    :param outputs:
    :param negation_dicts:
    :param concept_miner_v:
    :param batch_mode:
    :param batch_size:
    :param batch_number:
    :param tracking_method:

    """
    if concept_miner_v in [1, 2]:
        negation_tuples = list(flatten(d.read() for d in negation_dicts))
        concept_entries = list(flatten(d.read() for d in dictionaries))
        mc = miner2.MinerCask(concept_entries, negation_tuples)

    elif concept_miner_v == 3:
        mc = FeatureMiner()

    else:
        raise ValueError('Invalid version for ConceptMiner: %d.' % concept_miner_v)

    for out in outputs:
        out.create_output()

    process(documents, outputs, mc, SentenceBoundary())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--json-config',
                        help='Json file containing configuration information.')
    args = parser.parse_args()
    parse_processor(args.json_config)


if __name__ == '__main__':
    main()
