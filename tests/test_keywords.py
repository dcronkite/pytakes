import pytest

from pytakes import MinerCollection, ConceptMiner
from pytakes.dict.textitem import process_text
from pytakes.iolib.txt import TxtDictionary


@pytest.mark.parametrize('text, rules, kwargs, expected', [
    ('Forest for the trees. A tree?', ['tree'], {'regex_variation': -1}, ['tree', 'tree']),
])
def test_concept_miner_keywords(text, rules, kwargs, expected):
    mc = MinerCollection()
    mc.add(ConceptMiner([TxtDictionary(*rules, **kwargs)]))
    concepts = [found for found, sentence in process_text(text, mc)][0]
    assert [concept.word for concept in concepts] == expected
