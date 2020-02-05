import os

from pytakes.run.simple_run import run


def do_simple_run_and_get_outdir(outfile, negation_file=None, **kwargs):
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, 'data', 'files')
    outdir = os.path.join(path, 'data', 'testout')
    concepts = os.path.join(path, 'data', 'concepts.csv')
    negex_path = os.path.join(path, 'data', negation_file) if negation_file else None
    run(indir, outdir, concepts,
        outfile=outfile, negex_path=negex_path,
        hostname='Eumaeus', **kwargs)
    return outdir


def test_simple_run_csv():
    outfile = 'concepts.csv'
    outdir = do_simple_run_and_get_outdir(outfile=outfile)
    with open(os.path.join(outdir, outfile)) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.csv')) as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl():
    outfile = 'concepts.jsonl'
    outdir = do_simple_run_and_get_outdir(outfile=outfile)
    with open(os.path.join(outdir, outfile)) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.jsonl')) as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl_negex_csv():
    outfile = 'concepts.negex.jsonl'
    outdir = do_simple_run_and_get_outdir(
        outfile=outfile,
        negation_file='negation.csv'
    )
    with open(os.path.join(outdir, outfile)) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.negex.jsonl')) as fh:
        expected = fh.read()
    assert actual == expected
