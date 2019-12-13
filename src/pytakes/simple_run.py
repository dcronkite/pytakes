import os

from pytakes.processor import TextItem

from pytakes.nlp.conceptminer import ConceptMiner

from pytakes.nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp.collections import MinerCollection
from pytakes.nlp.statusminer import StatusMiner


def process(file, mc: MinerCollection):
    with open(file, encoding='utf8') as fh:
        ti = TextItem(fh.read())
    yield from mc.parse(ti)


def run(input_dir, output_dir, keyword_file):
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(ConceptMiner(dictionaries))
    mc.add(StatusMiner(negation_dicts))
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            with open(os.path.join(output_dir, f'{file}.tsv'), 'w', encoding='utf8') as out:
                for result in process(os.path.join(output_dir, file)):
                    out.write('\t'.join(str(x) for x in result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-i', '--input-dir', dest='input_dir')
    parser.add_argument('-o', '--output-dir', dest='output_dir')
    parser.add_argument('-k', '--keyword-file', dest='keyword_file')
    args = parser.parse_args()
