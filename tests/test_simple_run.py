from pathlib import Path

from pytakes.run.simple_run import run


def do_simple_run_and_get_outdir(outfile, negation_file=None, **kwargs):
    path = Path(__file__).absolute().parent
    indir = path / 'data' / 'files'
    outdir = path / 'data' / 'testout'
    concepts = path / 'data' / 'concepts.csv'
    negex_path = path / 'data' / negation_file if negation_file else None
    run(indir, outdir, concepts,
        outfile=outfile, negex_path=negex_path,
        hostname='Eumaeus', **kwargs)
    return outdir


def test_simple_run_csv():
    outfile = 'concepts.csv'
    outdir = do_simple_run_and_get_outdir(outfile=outfile)
    with open(outdir / outfile) as fh:
        actual = fh.read()
    with open(outdir / 'expected.csv') as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl():
    outfile = 'concepts.jsonl'
    outdir = do_simple_run_and_get_outdir(outfile=outfile)
    with open(outdir / outfile) as fh:
        actual = fh.read()
    with open(outdir / 'expected.jsonl') as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl_negex_csv():
    outfile = 'concepts.negex.jsonl'
    outdir = do_simple_run_and_get_outdir(
        outfile=outfile,
        negation_file='negation.csv'
    )
    with open(outdir / outfile) as fh:
        actual = fh.read()
    with open(outdir / 'expected.negex.jsonl') as fh:
        expected = fh.read()
    assert actual == expected
