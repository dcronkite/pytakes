from pathlib import Path

import pytest

from pytakes import CsvDictionary
from pytakes import MinerCollection
from pytakes import ConceptMiner
from pytakes import StatusMiner


@pytest.fixture
def path():
    return Path(__file__).absolute().parent


@pytest.fixture
def concept_file(path):
    return path / 'data' / 'concepts.csv'


def test_statusminer_negated():
    s = StatusMiner()
    negations = s.mine('no evidence of anything', 0)
    assert len(negations) == 1


def test_statusminer_hypothetical():
    s = StatusMiner()
    negations = s.mine('if he wants to', 0)
    assert len(negations) == 1


def test_negated_sentence(concept_file):
    mc = MinerCollection()
    mc.add(ConceptMiner([CsvDictionary(concept_file)]))
    mc.add(StatusMiner())
    concepts, sentence = mc.parse_sentence('no bad weather', offset=0)
    for concept in concepts:
        assert concept.is_negated()


def test_improbable_sentence(concept_file):
    mc = MinerCollection()
    mc.add(ConceptMiner([CsvDictionary(concept_file)]))
    mc.add(StatusMiner())
    concepts, sentence = mc.parse_sentence('no evidence of bad weather', offset=0)
    for concept in concepts:
        assert concept.is_improbable()


def test_hypothetical_sentence(concept_file):
    mc = MinerCollection()
    mc.add(ConceptMiner([CsvDictionary(concept_file)]))
    mc.add(StatusMiner())
    concepts, sentence = mc.parse_sentence('if there is bad weather', offset=0)
    for concept in concepts:
        assert concept.is_hypothetical()
