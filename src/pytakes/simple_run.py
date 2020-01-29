import os
from datetime import datetime

from pytakes import CsvDictionary, CsvOutput, TextItem, JsonlOutput
from pytakes import ConceptMiner, SentenceBoundary, MinerCollection, StatusMiner


def process(file, mc: MinerCollection):
    with open(file, encoding='utf8') as fh:
        ti = TextItem(fh.read().split('\n\n'))
    for res, sent in mc.parse(ti):
        yield res, sent


def output_context_manager(outfile, **kwargs):
    if outfile.endswith('jsonl'):
        return JsonlOutput(outfile, **kwargs)
    elif outfile.endswith('csv'):
        return CsvOutput(outfile, **kwargs)
    else:
        raise ValueError(f'Unrecognized file type: {outfile}')


def run(input_dir, output_dir, *keyword_files, outfile=None, negex_version=1,
        negex_path=None, skip_negex=False, hostname=None):
    """

    :param hostname: this is mostly for testing so that the output won't be machine-dependent
    :param skip_negex: don't run negex
    :param input_dir:
    :param output_dir:
    :param keyword_files:
    :param outfile:
    :param negex_version:
    :param negex_path: if included, will ignore table (will only use file)
    :return:
    """
    mc = MinerCollection(ssplit=SentenceBoundary().ssplit)
    mc.add(ConceptMiner([CsvDictionary(file) for file in keyword_files]))
    if not skip_negex:
        mc.add(StatusMiner(tablename=f'status{negex_version}', path=negex_path))
    if not outfile:
        outfile = 'extracted_concepts_{}.jsonl'.format(datetime.now().strftime('%Y%m%d_%H%M%S'))
    with output_context_manager(outfile, path=output_dir, metalabels=['file'], hostname=hostname) as out:
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
    parser.add_argument('--negex-version', dest='negex_version', default=1, type=int)
    parser.add_argument('--skip-negex', dest='skip_negex', action='store_true', default=False)
    parser.add_argument('--negex-path', dest='negex_path', default=None,
                        help='Specify csv file to use for negation rather than default.')
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, *args.keyword_files,
        outfile=args.outfile, negex_version=args.negex_version,
        skip_negex=args.skip_negex)
