"""
 # <p>Title: Sentence Boundary program </p>
 # <p>Create Date: 16:00:49 03/21/11</p>
 # <p>Copyright: Copyright (c) Department of Biomedical Informatics </p>
 # <p>Company: Vanderbilt University </p>
 # @author Yonghui Wu
 # @version 1.2
 # <p>Description: This program is used to detect sentence boundary and format each sentence as a single line </p>
 # Input: 1: English_dictionary 2: Abbreviation_dictionary 3: input_dir 4: output_dir
 # Output: Each file in the file_list will be processed by this sentence boundary tool,
 the out put will be generated in output directory with name: "file_name.sent"

Modified so that it will:
    1. read input from database
    2. parse sentences as parameters (a string/list) and return the result
    3. this will require a class-like interface
    
Edited: 2may13
Editor: David Cronkite, GHRI
"""
import re
import sqlite3
import pkg_resources


class SentenceBoundary(object):
    def __init__(self, ignorecase=True, config=None, debug=False):
        """

        :param ignorecase: case insensitive (default=True)
        :param config: dictionary which may contain the following keys
        .. note::
            prep -- list of prepositions
            det -- list of determiners
            conj -- list of conjunctions
            non_stop_punct -- list of stop punctuation
            sentence_word -- list of sentence words
            knuthus -- list of knuthus words
            abbrevs -- list of abbreviation words

        :param debug: enable debug mode (default=False)
        :return:
        """
        self.prep = {'about', 'above', 'across', 'after', 'against', 'aka', 'along', 'and', 'anti', 'apart', 'around',
                     'as', 'astride', 'at', 'away', 'because', 'before', 'behind', 'below', 'beneath', 'beside',
                     'between', 'beyond', 'but', 'by', 'contra', 'down', 'due to', 'during', 'ex', 'except',
                     'excluding', 'following', 'for', 'from', 'given', 'in', 'including', 'inside', 'into', 'like',
                     'near', 'nearby', 'neath', 'of', 'off', 'on', 'onto', 'or', 'out', 'over', 'past', 'per', 'plus',
                     'since', 'so', 'than', 'though', 'through', 'til', 'to', 'toward', 'towards', 'under',
                     'underneath', 'versus', 'via', 'where', 'while', 'with', 'within', 'without', 'also'}
        self.det = {'a', 'an', 'the'}
        self.conj = {'and', 'or', 'but', 'if', 'nor', 'for', 'except', 'although', 'no'}
        self.non_stop_punct = {}
        self.sentence_word = {'we', 'us', 'patient', 'denies', 'reveals', 'no', 'none', 'he', 'she', 'his', 'her',
                              'they', 'them', 'is', 'was', 'who', 'when', 'where', 'which', 'are', 'be', 'have', 'had',
                              'has', 'this', 'will', 'that', 'the', 'to', 'in', 'with', 'for', 'an', 'and', 'but', 'or',
                              'as', 'at', 'of', 'have', 'it', 'that', 'by', 'from', 'on', 'include'}

        if config and 'knuthus' in config and 'abbrevs' in config:
            self.knuthus = {}
            self.abbrevs = {}
        else:
            conn = sqlite3.connect(pkg_resources.resource_filename('pytakes.nlp', 'data/ssplit.db'))
            cur = conn.cursor()
            cur.execute('SELECT abbr FROM abbreviations')
            self.abbrevs = {x[0] for x in cur.fetchall()}
            cur.execute('SELECT word FROM knuthus')
            self.knuthus = {x[0] for x in cur.fetchall()}

        for el in config or []:
            setattr(self, el, self.load_set_lower(config[el]))

        self.abbrevs -= self.knuthus  # remove duplicates
        self.ignorecase = ignorecase
        self.debug = debug

    def ssplit(self, text, debug=False):
        # debug outputs print statements
        debug_ = (debug or self.debug)

        # sentences = []
        text = self.prepare_text(text)
        i = -1
        while i + 1 < len(text):
            i += 1
            txt = text[i]
            words = txt.split()
            tmp = ''
            for j, word in enumerate(words):
                pos = self.has_dot(word)
                if pos >= 0:
                    dot_num = self.num_dot(word)
                    if dot_num == 1:
                        if self.is_stop_punct(word):  # single dot
                            tmp += word + '\n'
                        # '.' begining, do not change
                        elif pos == 0:
                            tmp += word + ' '
                        # end of word
                        elif pos == len(word) - 1:
                            if self.is_num_list(word):
                                if j == 0:  # 1. Percocet 5/325 one p.o.
                                    tmp += word + ' '
                                else:  # postoperative day 3.
                                    tmp += word[:-1] + ' .\n'
                            # afebrile .
                            elif (word[:-1].lower() not in self.abbrevs and
                                    word.lower() not in self.abbrevs):
                                tmp += (word[:-1] + ' .\n')
                            else:  # abbreviations
                                if j + 1 < len(words):
                                    nword = words[j + 1]
                                else:
                                    nword = ''
                                # elevation MI. The patient was
                                if (len(nword) > 0 and
                                        self.isupper(nword[0], True) and
                                    # 1.0 MM. C) LEFT BREAST, ...
                                    # added by djc 30jul13
                                        (nword.lower() in self.sentence_word or
                                            (2 <= len(nword) <= 3 and
                                             nword[0].isalpha() and
                                             nword[-1] == ')'
                                             )
                                         )):
                                    tmp += word + '\n'
                                else:
                                    tmp += word + ' '
                        else:
                            lword, rword = word.split('.')
                            if (self.isupper(rword[0], True) and
                                    (rword in self.sentence_word or
                                     rword.lower() in self.knuthus)):
                                tmp += lword + '.\n' + rword + ' '
                            else:
                                tmp += word + ' '

                    else:
                        # "CK-MB of 9.1. His ..."
                        if word[-1] == '.':
                            if self.is_digit(word[:-1]):
                                tmp += word[:-1] + ' .\n'
                            else:  # "without need for O.T. or P.T.  He is"
                                if j + 1 < len(words):
                                    nword = words[j + 1]
                                else:
                                    nword = ''

                                if (len(nword) > 0 and
                                        self.isupper(nword[0], True) and
                                        nword.lower() in self.sentence_word):
                                    tmp += word + '\n'
                                else:
                                    tmp += word + ' '
                        else:
                            tmp += word + ' '

                else:  # normal word
                    tmp += word + ' '

            # end for j, word
            tmp = tmp.strip()
            if i + 1 < len(text):
                words = text[i + 1].split()
                nword = words[0]
                words = tmp.split()
                eword = words[-1].lower()
                # handle 'Page : '
                if ((len(txt) > 6 and
                        txt[:6].lower() == 'page :') or
                        (len(text[i + 1]) > 6 and
                            text[i + 1].lower() == 'page :')):
                    text[i] = (tmp.strip() + '\n')
                elif tmp[-1] == '.':
                    if (len(tmp) >= 2 and
                            tmp[-2] != ' ' and
                            not (nword == '-' or
                                 self.is_num_list(nword) or
                                 self.isupper(nword[0]))):
                        text[i] = (tmp.strip() + ' ')
                    else:
                        text[i] = (tmp.strip() + '\n')
                elif text[i][-1] != '.' and txt[-1] != ':':
                    # ends in prep, conj, det, and non_stop_punct
                    if (eword in self.prep or eword in self.det or
                            eword in self.non_stop_punct or eword in self.conj):
                        text[i] = (tmp.strip() + ' ')
                    elif not (nword == '-' or
                              self.is_num_list(nword) or
                              self.isupper(nword[0])):
                        text[i] = (tmp.strip() + ' ')
                    else:
                        text[i] = (tmp.strip() + '\n')
                else:
                    text[i] = (tmp.strip() + '\n')

            else:
                text[i] = tmp
        # end for i, txt
        if text:
            text[-1] += '\n'
        for group in text:
            for sentence in group.split('\n'):
                if sentence.strip():
                    yield sentence

    def isupper(self, word, default=False):
        if self.ignorecase:
            return default
        return word.isupper()

    def load_set_lower(self, lst):
        """
        Load dictionary in to a set, convert into lowercase.
        :param lst:
        """
        sett = set()
        for line in lst:
            line = line[0].strip()
            if len(line) > 0:
                sett.add(line.lower())
        return sett

    def num_dot(self, word):
        """
        return the number of dot in word
        :param word:
        """
        i = 0
        for w in word:
            if w == '.' or word[i] == '!' or word[i] == '?' or word[i] == ';':
                i += 1
        return i

    def has_dot(self, word):
        """
        Return the position of '.' in a word. -1 denote there are no '.' appeared
        :param word:
        """
        i = 0
        lenn = len(word)
        while i < lenn:
            if word[i] == '.' or word[i] == '!' or word[i] == '?' or word[i] == ';':
                return i
            i += 1
        return - 1

    def remove_double_star(self, line):
        """
        Some auto - inserted patterns in discharge summaries
        :param line:
        """
        pattern1 = r'\*\*NAME\[.{0,20}\]'
        return re.sub(pattern1, '**NAME**', line)

    def prepare_text(self, text):
        """
        Read text in to list,  remove the empty lines
        Parameters:
            text - string of text to be split
        Return:
            result - list of strings from text
            :param text:
        """
        result = []
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 0:
                line = self.remove_double_star(line)
                line = self.clean(line)
                line = self.seperate_puncts(line)
                line = re.sub(r'[ ]+', ' ', line)
                line = line.strip()
                if len(line) > 0:
                    result.append(line)
        return result

    def seperate_puncts(self, line):
        """
        separate punctuations from words,  except '.'
        :param line:
        """
        linee = ''
        for w in line:
            if self.is_punct(w):
                if len(linee) > 0 and linee[-1] != ' ':
                    linee = linee + ' ' + w + ' '
                else:
                    linee = linee + w + ' '
            else:
                linee = linee + w
        return linee.strip()

    def is_digit(self, word):
        """
        Identify all numbers
        :param word:
        """
        if re.match(r'[+-]?\d*[.]?\d+$', word):  # all number
            return True
        return False

    def is_num_list(self, word):
        """
        for list like:  1.   2.
        :param word:
        """
        if re.match(r'\d+\.$', word):  # num list
            return True
        return False

    def is_punct(self, w):
        """
        indentify the punctuation
        :param w:
        """
        if w == ',' or w == '?' or w == '!' or w == '"' or w == ';' or w == ':':
            # '.' and '+' used in ABBR
            return True
        else:
            return False

    def clean(self, sentence):
        """
        Clean text: replace '[ ]+' into '[ ]'; remove '^[ ]+' and '[ ]+$'
        :param sentence:
        """
        sentence = re.sub(r'&amp;', '&', sentence)
        sentence = re.sub(r'&gt;|&gt[ ];|&lt;|&lt[ ];', ' ', sentence)
        sentence = re.sub(r'\'s|\'S', ' \'s', sentence)
        sentence = re.sub(r'[ ]+', ' ', sentence)
        return sentence

    def get_ave_len(self, text):
        """
        get the average length of all the lines
        :param text:
        """
        lenn = len(text)
        avel = 0
        for line in text:
            avel += len(line)
        return avel / lenn

    def is_stop_punct(self, w):
        """
        These puncts are definitely a sentence boundary
        :param w:
        """
        if w == '?' or w == '!' or w == '.' or w == ';':
            return True
        else:
            return False
