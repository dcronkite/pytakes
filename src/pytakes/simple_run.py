import os
from datetime import datetime

from pytakes.io.csv import CsvDictionary, CsvOutput
from pytakes.dict.textitem import TextItem

from pytakes.nlp.conceptminer import ConceptMiner

from pytakes.nlp.sentence_boundary import SentenceBoundary

from pytakes.nlp.collections import MinerCollection
from pytakes.nlp.statusminer import StatusMiner


def process(file, mc: MinerCollection):
    with open(file, encoding='utf8') as fh:
        ti = TextItem(fh.read())
    for res, sent in mc.parse(ti):
        yield res, sent


def run(input_dir, output_dir, *keyword_files, outfile=None, negex_version=1):
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(ConceptMiner([CsvDictionary(file) for file in keyword_files]))
    mc.add(StatusMiner(tablename=f'status{negex_version}'))
    if not outfile:
        outfile = 'extracted_concepts_{}.csv'.format(datetime.now().strftime('%Y%m%d_%H%M%S'))
    out = CsvOutput(outfile, output_dir, metalabels=['file'])
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            for results, sent in process(os.path.join(input_dir, file), mc):
                for result in results:
                    out.writerow(result, meta=[file], text=sent)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-i', '--input-dir', dest='input_dir', required=True)
    parser.add_argument('-o', '--output-dir', dest='output_dir', required=True)
    parser.add_argument('-k', '--keyword-files', nargs='+', dest='keyword_files', required=True)
    parser.add_argument('--outfile', dest='outfile', default=None)
    parser.add_argument('--negex_version', dest='negex_version', default=1, type=int)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, *args.keyword_files,
        outfile=args.outfile, negex_version=args.negex_version)
