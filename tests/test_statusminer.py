from pytakes.nlp.statusminer import StatusMiner


def test_statusminer_annotates():
    s = StatusMiner()
    negations = s.mine('no evidence of anything', 0)
    assert len(negations) == 1
