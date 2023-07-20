from pytakes import StatusMiner, Word, Negation, Term, TextItem, MinerCollection, ConceptMiner
from pytakes.dict.textitem import process_textitem
from pytakes.iolib.txt import TxtDictionary


def test_negation_bidirectional():
    miner = StatusMiner(rules=[])
    terms = [
        Term('I', 0, 1, 'C01', 1),
        Word('have', 2, 6),
        Negation('no', 7, 9, 'negn', 3),
        Term('beer', 10, 14, 'C02', 2),
    ]
    miner.postprocess(terms)
    assert terms[0].is_negated()
    assert terms[-1].is_negated()


def test_negation_forward():
    miner = StatusMiner(rules=[])
    terms = [
        Term('I', 0, 1, 'C01', 1),
        Word('have', 2, 6),
        Negation('no', 7, 9, 'negn', 2),
        Term('beer', 10, 14, 'C02', 2),
    ]
    miner.postprocess(terms)
    assert not terms[0].is_negated()
    assert terms[-1].is_negated()


def test_negation_backward():
    miner = StatusMiner(rules=[])
    terms = [
        Term('I', 0, 1, 'C01', 1),
        Word('have', 2, 6),
        Negation('no', 7, 9, 'negn', 1),
        Term('beer', 10, 14, 'C02', 2),
    ]
    miner.postprocess(terms)
    assert terms[0].is_negated()
    assert not terms[-1].is_negated()


def test_negation_with_punct():
    miner = StatusMiner(rules=[('c/o', 'negn', 3)])
    assert len(miner.mine('pt c/o', 0)) == 1
    assert len(miner.mine('pt c / o', 0)) == 0


def test_negation_with_punct2():
    miner = StatusMiner(rules=[('c / o', 'negn', 3)])
    assert len(miner.mine('pt c/o', 0)) == 0
    assert len(miner.mine('pt c / o', 0)) == 1


def test_negation_with_punct3():
    miner = StatusMiner(rules=[(r'c\s*/\s*o', 'negn', 3)])
    assert len(miner.mine('pt c/o', 0)) == 1
    assert len(miner.mine('pt c / o', 0)) == 1


def test_negation_end_scope_conj():
    miner = StatusMiner(rules=[])
    terms = [
        Term('I', 0, 1, 'C01', 1),
        Word('have', 2, 6),
        Negation('no', 7, 9, 'negn', 3),
        Term('beer', 10, 14, 'C02', 2),
        Negation('or', 15, 17, 'conj', 0),
        Term('wine', 18, 22, 'C02', 3),
    ]
    miner.postprocess(terms)
    assert terms[0].is_negated()
    assert terms[-3].is_negated()  # negates 'beer'
    assert not terms[-1].is_negated()  # 'or' blocks 'wine' from being negated


def test_default_negation():
    ti = TextItem(['I am not happy.'])
    mc = MinerCollection()
    mc.add(ConceptMiner([TxtDictionary('happy', 'sad')]))
    mc.add(StatusMiner())
    concepts = [found for found, sentence in process_textitem(ti, mc)][0]
    assert len(concepts) == 1  # 'happy'
    assert concepts[0].type_ == 'concept'
    assert concepts[0].get_certainty() == 0
    assert concepts[0].qualifiers == ['not']
