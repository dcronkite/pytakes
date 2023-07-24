import pytest

from pytakes import MinerCollection, ConceptMiner
from pytakes.dict.textitem import process_text
from pytakes.iolib.txt import TxtDictionary


@pytest.mark.parametrize('text, rules, kwargs, expected', [
    # concepts will be left alone and compiled without escaping
    ('Forest for the trees. A tree?', ['tree'], {'regex_variation': -1}, ['tree', 'tree']),
    ('Forest for the trees. A tree?', ['tree'], {'regex_variation': 0}, ['trees', 'tree']),
    ('Do you always write such charming long letters to her?', ['letters?'], {'regex_variation': 0}, ['letters']),
    ('charming long letters', ['letters?', r'charm\w+ letters?'], {'regex_variation': 0},
     ['charming long letters', 'letters']),
    # show 1 deletion
    ('Patient has anapylaxis', ['anaphylaxis'], {'regex_variation': 2}, ['anapylaxis']),
    # fails since requires 2 deletions and 1 insertion
    ('Patient has anafylaxis', ['anaphylaxis'], {'regex_variation': 2}, []),
    # but this works with regex variation of 3
    ('Patient has anafylaxis', ['anaphylaxis'], {'regex_variation': 3}, ['anafylaxis']),
])
def test_concept_miner_keywords(text, rules, kwargs, expected):
    mc = MinerCollection()
    mc.add(ConceptMiner([TxtDictionary(*rules, **kwargs)]))
    concepts = [found for found, sentence in process_text(text, mc)][0]
    assert [text[concept.begin:concept.end] for concept in concepts] == expected
