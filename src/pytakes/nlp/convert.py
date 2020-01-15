"""
David Cronkite

Purpose:
    Automatically create a minimal set of RegExs from a sequence of terms.
    The identity of the terms is retained.
"""
# regex should replace/expand re
# may require a new flag to get
# default regex behavior after this
# transformation
import regex as re


def get_affix_morphs():
    """
    list of tuple(regex, replacement string, count) for modifying 
        the front of a term
    count represents the number of letters which are becoming
        optional (not _new_ optional ones)
    """
    return [(re.compile(r'\bun(\S{3,})'), r'(non|un|in|im)\g<1>', 2, 11),  # un
            (re.compile(r'\bnon(\S{3,})'), r'(non|un|in|im)\g<1>', 3, 11)]  # non


def get_medial_morphs():
    """
    list of tuple(regex, replacement string, count) for modifying 
        the middle of a term
    count represents the number of letters which are becoming
        optional (not _new_ optional ones)
    """
    return [(re.compile(r'\b(\S+)-(\S+)\b'), r'\g<1>(-| )?\g<2>', 1)]  # hyphen


def get_suffix_morphs():
    """
    list of tuple(regex, replacement string, count) for modifying 
        the end of a term
    count represents the number of letters which are becoming
        optional (not _new_ optional ones)
    """
    return [(re.compile(r'(\S{3,})ous\b'), r'\g<1>(ous)?', 3),  # -ous
            (re.compile(r'(\S{3,})al\b'), r'\g<1>(al|um)?', 2),  # -al
            (re.compile(r'(\S{1,})y\b'), r'\g<1>(y|ie)?', 1),  # -y pl.
            (re.compile(r'(\S{2,})oma\b'), r'\g<1>oma(ta|l|al)?', 0),  # -oma
            (re.compile(r'(\S{3,})ic\b'), r'\g<1>(ic)?', 2),  # -ic
            (re.compile(r'(\S{3,})oid\b'), r'\g<1>(oid|al)?', 3),  # -oid
            (re.compile(r'(\S{3,})ed\b'), r'\g<1>ed?', 1),  # -ed
            (re.compile(r'(\S{3,})ar\b'), r'\g<1>(ar)?', 2),  # -ar
            (re.compile(r'(\S{3,})is\b'), r'\g<1>(is|ic|es)?', 2),  # -is
            (re.compile(r'(\S{3,})ing\b'), r'\g<1>(ing|ed|e)?', 3),  # -ing
            (re.compile(r'(\S{3,})(s|t)ive\b'), r'\g<1>\g<2>(ive|ion)?', 3)]  # -sive


def get_final_morphs():
    """
    DEPRECATED -- if-elif-else expression more effective
        since difficult to sub at the end (after non-letters)
        
    Accounts for plurals.
    list of tuple(regex, replacement string, count) for computing
        the plural of a term
    count represents the number of letters which are becoming
        optional (not _new_ optional ones)
    """
    return [(re.compile(r'\b(\S+)s(\W*)\b'), r'\g<1>\g<2>s(es)?', 0),  # pl='es'
            (re.compile(r'\b(\S+)o(\W*)\b'), r'\g<1>\g<2>o(e?s)?', 0),  # pl='es'
            (re.compile(r'\b(\S+)(\W*)\b'), r'\g<1>\g<2>s?', 0)]  # pl='s'


def convert_to_regex(strings_ids_rxvar, convert_all=True,
                     affixmorphs=None, suffixmorphs=None,
                     medialmorphs=None, finalmorphs=None):
    """
    Takes a list of string-id tuples which are the words which
        need to be converted to regular expressions.
        The id part should be a unique identifier.
    Duplicate regexes will not be included. Duplicates
        are defined by whether or not a previous regex
        matches a succeeding one.
        
    Parameters:
        string_ids_settings: list of (string, id, wdOrder ) in which 
            string is to be converted to regex;
            order is important as the strings are
            converted to regexes in list order, and
            any following strings which are matched
            by the previous regexes will not be included
        degree of regex variation-
                    -1: no variation at all (no prefixes/suffixes)
                    0: no variation; words must be exact
                    1: minimal variation
                    2: moderate variation
                    3: flexible
        convert_all=True: if false, all strings will be
            converted to regexes regardless of a previous
            regex matching it
            :param strings_ids_rxvar:
            :param convert_all:
            :param affixmorphs:
            :param suffixmorphs:
            :param medialmorphs:
            :param finalmorphs:
    """
    if not affixmorphs:
        affixmorphs = get_affix_morphs()
    if not medialmorphs:
        medialmorphs = get_medial_morphs()
    if not suffixmorphs:
        suffixmorphs = get_suffix_morphs()

    regexes = []  # [(regex, id), ...]
    updated_ids = {}  # new_id -> old_id
    for string, id_, regex_variation in strings_ids_rxvar:
        string = string.replace('(', '').replace(')', '')
        string = string.replace('*', r'\w*')
        if regex_variation == -1:
            regexes.append((re.compile(r'\b{}\b'.format(string), re.I), id_))
            continue

        if not convert_all:
            # see if string is matched by previously-
            #    created RegEx
            found = False
            for rx, rx_id in regexes:
                if rx.match(string):
                    # print string,'duplicate of',rx,rx_id
                    found = True
                    if rx_id not in updated_ids:
                        updated_ids[rx_id] = {rx_id}
                    updated_ids[rx_id].add(id_)
                    break
            if found:
                continue  # Duplicate RegEx was found

        length = len(string)
        start_idx = 0  # ensure first letter is unable to change
        orig_string = string

        # 1) convert string to regex
        # a) convert any prefix
        for morph, repl, L, rLen in affixmorphs:
            if morph.match(string):
                string = morph.sub(repl, string)
                length -= L
                start_idx += rLen  # advance start index to letter after prefix
                break
        # b) convert any medial elements
        for morph, repl, L in medialmorphs:
            if morph.match(string):
                string = morph.sub(repl, string)
                length -= L
                break
        # c) convert any suffix
        for morph, repl, L in suffixmorphs:
            if morph.match(string):
                string = morph.sub(repl, string)
                length -= L
                break
        # d) add final elements
        if len(orig_string) > 2:
            if orig_string[-1] == 's':
                string += r'(es)?'
            elif orig_string[-1] == 'o':
                string += r'(e?s)?'
            else:
                string += r's?'

        # 2) add Error permissions
        length -= 1  # removing the first term
        # FLEXIBLE
        if regex_variation == 3:
            if length in [4, 5, 6]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){i<2,d<2}')
            elif length in [7, 8, 9]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){1i+1d<4}')
            elif length >= 10:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){e<4}')
        # MODERATE
        elif regex_variation == 2:
            if length in [4, 5, 6]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){s<2}')
            elif length in [7, 8, 9]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){1i+1d<3}')
            elif length >= 10:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){e<3}')
        # MINIMAL
        elif regex_variation == 1:
            if length in [4, 5, 6]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){s<2}')
            elif length in [7, 8, 9]:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){1i+1d<2}')
            elif length >= 10:
                string = (string[:start_idx + 1] + '(' + string[start_idx + 1:] + '){e<2}')
        # NONE
        elif regex_variation == 0:
            pass

        # 3) add word boundary
        string = r'\b' + string + r'\b'

        # 4) compile string to regex
        rx = re.compile(string, re.V1 | re.I)
        # try:
        #     assert rx.match(orig_string)
        # except AssertionError:
        #     raise ValueError(r'Regex {} failed to match original string "{}".'.format(rx, orig_string))
        regexes.append((rx, id_))

    return regexes, updated_ids
