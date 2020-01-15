import os

from pytakes.simple_run import run


def test_simple_run_csv():
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, 'data', 'files')
    outdir = os.path.join(path, r'data', 'testout')
    concepts = os.path.join(path, r'data', 'concepts.csv')
    run(indir, outdir, concepts, outfile='concepts.csv')
    with open(os.path.join(outdir, 'concepts.csv')) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.csv')) as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl():
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, 'data', 'files')
    outdir = os.path.join(path, 'data', 'testout')
    concepts = os.path.join(path, 'data', 'concepts.csv')
    run(indir, outdir, concepts, outfile='concepts.jsonl')
    with open(os.path.join(outdir, 'concepts.jsonl')) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.jsonl')) as fh:
        expected = fh.read()
    assert actual == expected


def test_simple_run_jsonl_negex_csv():
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, 'data', 'files')
    outdir = os.path.join(path, 'data', 'testout')
    concepts = os.path.join(path, 'data', 'concepts.csv')
    negex_file = os.path.join(path, 'data', 'negation.csv')
    run(indir, outdir, concepts, outfile='concepts.negex.jsonl', negex_path=negex_file)
    with open(os.path.join(outdir, 'concepts.negex.jsonl')) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.negex.jsonl')) as fh:
        expected = fh.read()
    assert actual == expected
