import os

from pytakes.simple_run import run


def test_complete():
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, r'data\files')
    outdir = os.path.join(path, r'data\testout')
    concepts = os.path.join(path, r'data\concepts.csv')
    run(indir, outdir, concepts, outfile='concepts.csv')
    with open(os.path.join(outdir, 'concepts.csv')) as fh:
        actual = fh.read()
    with open(os.path.join(outdir, 'expected.csv')) as fh:
        expected = fh.read()
    assert actual == expected
