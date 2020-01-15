import os

from pytakes.nlp.statusminer import StatusMiner


def test_load_from_csv():
    path = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(path, 'data', 'negation.csv')
    rules = list(StatusMiner.load_negex_from_csv(csv_file))
    assert len(rules) == 12
    regex_loaded = False  # was regular expression correctly loaded
    for negex, type_, direction in rules:
        assert len(negex) > 0
        if r'\s' in negex:
            regex_loaded = True
        assert len(type_) == 4
        assert direction in {0, 1, 2, 3}
    assert regex_loaded
