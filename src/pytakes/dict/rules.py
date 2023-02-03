import copy
from itertools import product

import regex as re

CUI_IDX, CAT_IDX, CONFIG_IDX = range(3)


class Config(list):
    def __init__(self, *args):
        if args:
            args = args[0]
        newiter = []
        for el in args:
            newiter.append([el])
        list.__init__(self, newiter)

    def add(self, lst):
        for idx, el in enumerate(lst):
            if self.__len__() > idx:
                self[idx] = self[idx] + el
            else:
                self.append(el)

    def get(self, idx, default, func=min):
        if self.__len__() > idx:
            try:
                res = func(x for x in self.__getitem__(idx) if x is not None)
            except ValueError:  # min() on empty list
                return default
            return res
        return default


def generate_combinations(rules, cats, generator):
    rows = []
    for cui, rule, configs in rules:
        if not cui:
            cui = generator.generate_cui()
        if not configs:
            configs = Config()
        cui = cui[:8]  # limit cui length to 8 characters
        lst = []
        start = 0
        for m in re.finditer(r'\[(?P<CATEGORY>\w+?)\]', rule):
            if m.start() > start:
                lst.append([rule[start: m.start()]])
            lst.append(cats[m.group('CATEGORY')])
            start = m.end()
        # final fencepost
        if start < len(rule) - 1:
            lst.append([rule[start:]])
        rows.append((cui, list(product(*lst)), configs))
    return rows


def build_rows(rows, generator):
    results = []
    for cui, c_rows, configs in rows:
        for row in c_rows:
            row_cui, row_configs, text = get_meta_for_row(cui, configs, row)
            # cui, fword, term, textlength, code, regexVariation, wordOrder
            insert = [None] * 8
            insert[0] = row_cui
            insert[2] = ' '.join((''.join(text).strip()).split())  # term
            insert[1] = insert[2].split(' ')[0]  # firstword
            # noinspection PyTypeChecker
            insert[3] = len(insert[2])  # textlength
            insert[4] = generator.generate_code()  # unique code
            # min is the most conservative parameter (in the following...)
            insert[5] = row_configs.get(0, default=1, func=min)  # regexVariation
            # max is the most conservative parameter in the following...
            insert[6] = row_configs.get(1, default=1, func=max)  # wordOrder
            # valence doesn't do anything yet...it needs to be 1
            insert[7] = row_configs.get(2, default=1, func=max)  # valence
            results.append(insert)
    return results


def get_meta_for_row(cui, configs, row):
    """
    get the min of each config
    NB: cui is ignored, and returns only the given CUI
        - I can't figure out how to make sense of
        word-level CUIs...which trumps the other?
    """
    text = []
    row_configs = copy.copy(configs)

    for el in row:
        if isinstance(el, (list, tuple)):
            row_cui, content, conf = el
            row_configs.add(conf)
            text.append(content)
            if not cui or cui.startswith('G'):
                cui = row_cui
        else:
            text.append(el)

    return cui, row_configs, text


#  RULES
def read_rules(rulefile, generator):
    rules = []
    with open(rulefile) as f:
        for line in f.readlines():
            line = line.strip()

            # remove comments
            if not line or line[0] == '#':
                continue
            elif '#' in line:
                line = line[:line.index('#')].strip()
            cui, rule, configs = parse_rule(line)
            generator.used_cui(cui)
            rules.append((cui, rule, configs))
    return rules


def parse_rule(line):
    # get optional cui
    if '==' in line:
        cui, rule = line.split('==')
        cui.strip()
    else:
        rule = line
        cui = None

    # get optional configs ## added v1.1
    if '%%' in rule:
        rule, configs = rule.split('%%')
        configs = Config([int(x) if x.strip() else None for x in configs.split(',')])
    else:
        configs = Config()
    return cui, rule.strip(), configs


#  CATEGORIES
def read_files(catfiles, categories):
    for file in catfiles:
        read_file(file, categories)
    return categories


def read_file(catfile, categories):
    with open(catfile) as f:
        cat = catfile.stem
        for line in f.readlines():
            line = line.strip()
            
            # remove comments
            if not line or line[0] == '#':
                continue
            elif '#' in line:
                line = line[:line.index('#')].strip()

            m = re.match(r'\[(\w+?)]', line)
            if m:  # found category name
                cat = m.group(1)
                if cat not in categories:
                    categories[cat] = []
                continue

            else:  # found names belonging to category
                names = read_cat(line)
                if cat not in categories:
                    categories[cat] = []
                categories[cat] += names


def read_cat(cats):
    """
    cats - list of lines in category file,
        name(||name2||...)%%config1,config2

    NB: cui== is ignored!!
    """
    names = []
    for cat in cats if isinstance(cats, list) else [cats]:
        cat = cat.strip()
        cui, cat, configs = parse_rule(cat)
        # divide line into separate synonyms
        names += [(cui, c.strip(), configs) for c in cat.split('||')]
    return names
