from pytakes.nlp.statusminer import StatusMiner, Word, Negation, Term


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
