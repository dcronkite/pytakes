import os

from pytakes.simple_run import run


def test_complete():
    path = os.path.dirname(os.path.abspath(__file__))
    indir = os.path.join(path, r'data\files')
    outdir = os.path.join(path, r'data\testout')
    concepts = os.path.join(path, r'data\concepts.csv')
    os.makedirs(outdir, exist_ok=True)
    run(indir, outdir, concepts)
