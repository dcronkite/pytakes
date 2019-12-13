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
from pytakes.nlp.collections import MinerCollection
from pytakes.nlp.conceptminer import ConceptMiner
from pytakes.nlp.statusminer import StatusMiner
from pytakes.parser import parse_processor
from pytakes.util.utils import flatten
from .util import mylogger
from .nlp.ngrams import FeatureMiner
from .nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp import conceptminer as miner2


class TextItem(object):
    """ Carries metainformation and text for a document
    """

    def __init__(self, text, meta_list=None):
        self.meta_ = tuple(meta_list) or ()
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
                logging.info('Completed: {:>5}.'.format(num))

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
