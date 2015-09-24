'''
 # <p>Title: Sentence Boundary program </p>
 # <p>Create Date: 16:00:49 03/21/11</p>
 # <p>Copyright: Copyright (c) Department of Biomedical Informatics </p>
 # <p>Company: Vanderbilt University </p>
 # @author Yonghui Wu
 # @version 1.2
 # <p>Description: This program is used to detect sentence boundary and format each sentence as a single line </p>
 # Input: 1: English_dictionary 2: Abbreviation_dictionary 3: input_dir 4: output_dir
 # Output: Each file in the file_list will be processed by this sentence boundary tool, the out put will be generated in output directory with name: "file_name.sent"
'''
 
'''
Modified so that it will:
    1. read input from database
    2. parse sentences as parameters (a string/list) and return the result
    3. this will require a class-like interface
    
Edited: 2may13
Editor: David Cronkite, GHRI
'''

import re

    
#This is the main procedure to process a single file 'fname'.
#Each line of the file is processed sequencially.
#For each line, first handle all the word with '.'; then handle the end of a line.
#If a '.' or the end of current line is a sentence boundary, insert a '\n' after them.


class SentenceBoundary(object):
    
    def __init__(self, cur, ignorecase=True, word_table='res_ss_word', abbr_table = 'res_ss_abbr', debug=False):
        '''
        Parameters:
            cur = dbi connection cursor
        '''
        self.prep = set(['about','above','across','after','against','aka','along','and','anti','apart','around','as','astride','at','away','because','before','behind','below','beneath','beside','between','beyond','but','by','contra','down','due to','during','ex','except','excluding','following','for','from','given','in','including','inside','into','like','near','nearby','neath','of','off','on','onto','or','out','over','past','per','plus','since','so','than','though','through','til','to','toward','towards','under','underneath','versus','via','where','while','with','within','without', 'also'])
        self.det = set(['a', 'an', 'the'])
        self.conj = set(['and','or','but','if','nor','for','except','although','no'])
        self.non_stop_punct = set([]) #set([',']) #set([',', ';'])
        self.sentence_word = set(['we','us','patient','denies','reveals','no','none','he','she','his','her','they','them','is','was','who','when','where','which','are','be','have','had','has','this','will','that','the','to','in','with','for','an','and','but','or','as','at','of','have','it','that','by','from','on','include'])
        self.knuthus = self.load_set_lower(cur.execute_return("SELECT * FROM %s" % word_table))
        self.abbr_dic = self.load_set_lower(cur.execute_return("SELECT * FROM %s" % abbr_table)) - self.knuthus
        self.ignorecase = ignorecase
        self.debug = debug
        
    def ssplit2(self, text, debug=False):
        # debug outputs print statements
        DEBUG = (debug or self.debug)
        
        i = 0
        text = self.prepare_text(text)
        while i <  len(text):
            if DEBUG: print 'line: ', i
            if DEBUG: print 'current line: ', text[i]
            
            words = text[i].split(' ')
            tmp = ''
            j = 0
            while j < len(words):
                word = words[j]
                pos = self.has_dot(word)
                if DEBUG: print "\t\tWORD:",word
                if pos >= 0:
                    dot_num = self.num_dot(word)
                    if dot_num == 1:
                        if self.is_stop_punct(word):  #single dot
                            tmp = tmp + word + '\n'
                        elif pos == 0: #'.' on the begining, keep it original,  do not change
                            tmp = tmp + word + ' ' 
                        elif pos == len(word) - 1: # on the end of word
                            if DEBUG: print 'j: ', j, 'dot end: ', word
                            
                            #print is_num_list(word)
                            #print not (is_num_list(word) and j == 0)
                            #print (word[:-1].lower() not in abbr_dic or word.lower() not in abbr_dic)
                            
                            # New sentence '3.': postoperative day 3.
                            # Not new sentence '1.': 1. Percocet 5/325 one p.o. every 4 hours p.r.n.
                            if self.is_num_list(word):
                                if j == 0: #1. Percocet 5/325 one p.o.
                                    tmp = tmp + word + ' ' 
                                else: #postoperative day 3.
                                    tmp = tmp + word[:-1] + ' ' + '.\n'
                                    
                            # afebrile .
                            elif word[:-1].lower() not in self.abbr_dic and word.lower() not in self.abbr_dic:
                                tmp = tmp + word[:-1] + ' ' + '.\n'
                            else: #abbreviations
                                if DEBUG: print 'abbr: ', word
                                if j + 1 < len(words):
                                    next_word = words[j + 1]
                                else:
                                    next_word = ''
                                #elevation MI. The patient was
                                if len(next_word) > 0 and next_word[0].isupper() and next_word.lower() in self.sentence_word:
                                    if DEBUG: print 'abbr add enter'
                                    tmp = tmp + word + '\n'
                                else:
                                    tmp = tmp + word + ' ' 
                        else: #'.' is on the center of a word. Do not handle this now. If the corpus contians too much
                            # go.The,  we have to handle this.
                            # the token has a '.' in the center.
                            
                            words_center = word.split('.')
                            right_word = words_center[1]
                            
                            if right_word[0].isupper() and ((right_word in self.sentence_word) or( right_word.lower() in self.knuthus) ):
                                tmp = tmp + words_center[0] + '.\n' + right_word + ' '
                            else: 
                                tmp = tmp + word + ' '
                            if DEBUG: print 'tmp: ', tmp
                    else: # for the dot_num > 1, almost all of them are abbreviations.
                        #Handle:  CK-MB of 9.1. His post
                        if word[-1] == '.':
                            if self.is_digit(word[:-1]):
                                tmp = tmp + word[:-1] + ' ' + '.\n'
                            else:
                                #Handle: condition without the need for O.T. or P.T.  He is being
                                if DEBUG: print 'multi dot: ', word
                                if j + 1 < len(words):
                                    next_word = words[j + 1]
                                else:
                                    next_word = ''

                                if len(next_word) > 0 and next_word[0].isupper() and next_word.lower() in self.sentence_word:
                                    if DEBUG: print 'multi dot add enter'
                                    tmp = tmp + word + '\n'
                                else:
                                    tmp = tmp + word + ' '
                                    
                        else: 
                            tmp = tmp + word + ' ' 
                else: # normal words,  just add it
                    tmp = tmp + word + ' ' 
            
                j = j + 1
                
            #handle the '\n' end of line
            #get the first word of next line

            tmp = tmp.strip(' ')
            if i + 1 < len(text):
                words = text[i + 1].split(' ')
                next_word = words[0]
                words = tmp.split(' ')
                last_word = words[-1]

                if DEBUG: print 'next word: ', next_word
                #print len(text[i]) > ave_len
                #print not is_num_list(next_word)
                #
                # Using the ave_len to discriminate the shot sentences, will cause problems to the normal sentences :
                #e.g., 
                #positive urine pregnancy test,BHCG of 43, and UDS + for cocaine.  An ultrasound\N
                #was obtained\N
                #in the ER which showed a tuboovarian abscess. She was admitted to benign\N
                #
                # However,  if there are too many short sentences, you should use this rule:  (len(text[i]) > ave_len)

                #The current line is:  "Page : 2" or next line is:  "Page : 2",  do not merge
                
            
                
                # handle the exceptions for 'Page : '
                if (len(text[i]) > 6 and text[i][:6].lower()== 'page :') or (len(text[i+1]) > 6 and text[i+1][:6].lower()== 'page :'):
                    text[i] = tmp.strip() + '\n'
                elif tmp[-1] == '.':
                    if DEBUG: 
                        print 'end with dot, the dot is part of abbreviation: e.g.,  Dr.'
                    if len(tmp) >= 2 and tmp[-2] !=  ' ' and ( not next_word == '-')\
                       and (not self.is_num_list(next_word)) and ( not next_word[0].isupper()):
                        text[i] = tmp.strip() + ' '
                    else: #lesion ., or next line could not be merged
                        text[i] = tmp.strip() + '\n'
                
                elif text[i][-1] != '.' and text[i][-1] != ':':
                    
                    #handle exceptions when the senctence is ended with words in prep, det and non_stop_punct
                    if last_word in self.prep or last_word in self.det or last_word in self.non_stop_punct or last_word in self.conj:
                        text[i] = tmp.strip() + ' '
                    elif ( not next_word == '-') and (not self.is_num_list(next_word)) and ( not next_word[0].isupper()): # 
                        text[i] = tmp.strip() + ' '
                    else:
                        text[i] = tmp.strip() + '\n'

                else:
                    if DEBUG: print 'add enter'
                    text[i] = tmp.strip() + '\n'
            i = i + 1
        return text
        
    def ssplit(self, text, debug= False):
        # debug outputs print statements
        DEBUG = (debug or self.debug)
        
        # sentences = []
        text = self.prepare_text(text)
        i = -1
        while i+1 < len(text):
            i += 1
            txt = text[i]
            if DEBUG: print 'LINE %d:'%i,txt
            
            words = txt.split()
            tmp = ''
            for j, word in enumerate(words):
                pos = self.has_dot(word)
                if DEBUG: print "\t\tWORD:",word
                if pos >= 0:
                    dot_num = self.num_dot(word)
                    if dot_num == 1:
                        if self.is_stop_punct(word): #single dot
                            tmp += word + '\n'
                        #'.' begining, do not change
                        elif pos == 0: 
                            tmp += word + ' '
                        # end of word
                        elif pos == len(word)-1:
                            if DEBUG: print '  %d, dot end: %s' % (j,word)
                            if self.is_num_list(word):
                                if j == 0: #1. Percocet 5/325 one p.o.
                                    tmp += word + ' '
                                else: #postoperative day 3.
                                    tmp += word[:-1] + ' .\n'
                            #afebrile .
                            elif (word[:-1].lower() not in self.abbr_dic
                                    and word.lower() not in self.abbr_dic):
                                tmp += (word[:-1] + ' .\n')
                            else: #abbreviations
                                if j+1 < len(words):
                                    nword = words[j+1]
                                else:
                                    nword = ''
                                #elevation MI. The patient was
                                if (len(nword) > 0 and 
                                        self.isupper(nword[0],True) and
                                            # 1.0 MM. C) LEFT BREAST, ...
                                            # added by djc 30jul13
                                            (nword.lower() in self.sentence_word or
                                                (len(nword) >= 2 and
                                                 len(nword) <= 3 and
                                                 nword[0].isalpha() and
                                                 nword[-1] == ')'
                                                )
                                            )
                                    ):
                                    tmp += word + '\n'
                                else:
                                    tmp += word + ' '
                        else:
                            Lword,Rword = word.split('.')
                            if (self.isupper(Rword[0],True) and
                                    ( Rword in self.sentence_word or
                                      Rword.lower() in self.knuthus)):
                                tmp += Lword + '.\n' + Rword + ' '
                            else:
                                tmp += word + ' '
                        
                    else:
                        # "CK-MB of 9.1. His ..."
                        if word[-1] == '.':
                            if self.is_digit(word[:-1]):
                                tmp += word[:-1] + ' .\n'
                            else: # "without need for O.T. or P.T.  He is"
                                if j+1 < len(words):
                                    nword = words[j+1]
                                else:
                                    nword = ''
                            
                                if (len(nword) > 0 and
                                        self.isupper(nword[0],True) and
                                        nword.lower() in self.sentence_word):
                                    tmp += word + '\n'
                                else:
                                    tmp += word + ' '
                        else:
                            tmp += word + ' '
            
                else: # normal word
                    tmp += word + ' '
            
            # end for j, word
            if DEBUG: print "TempVar:",tmp
            tmp = tmp.strip()
            if i+1 < len(text):
                words = text[i+1].split()
                nword = words[0]
                words = tmp.split()
                eword = words[-1].lower()
                # handle 'Page : '
                if (( len(txt) > 6 and
                      txt[:6].lower() == 'page :') or
                    ( len(text[i+1]) > 6 and
                      text[i+1].lower() == 'page :')
                    ):
                    text[i] = (tmp.strip() + '\n')
                elif tmp[-1] == '.':
                    if ( len(tmp) >= 2 and
                         tmp[-2] != ' ' and
                         not (nword == '-' or
                              self.is_num_list(nword) or
                               self.isupper(nword[0]))
                        ):
                        text[i] = (tmp.strip() + ' ')
                    else:
                        text[i] = (tmp.strip() + '\n')
                elif text[i][-1] != '.' and txt[-1] != ':':
                    #ends in prep, conj, det, and non_stop_punct
                    if (eword in self.prep or eword in self.det or
                        eword in self.non_stop_punct or eword in self.conj
                        ):
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
        # print text
        # print 'JOIN:',''.join(text)
        # print 'SPLIT:',''.join(text).split('\n')
        return text
            
    def isupper(self,word,default=False):
        if self.ignorecase:
            return default
        return word.isupper()

    def load_set_lower(self,lst):
        '''
        Load dictionary in to a set, convert into lowercase.  
        '''
        sett = set()
        for line in lst:
            line = line[0].strip()
            if len(line) > 0:
                sett.add(line.lower())
        return sett
    
    def num_dot(self, word):
        '''
        return the number of dot in word
        '''
        i = 0
        for w in word:
            if w == '.' or word[i] == '!' or word[i] == '?' or word[i] == ';':
                i = i + 1
        return i

    def has_dot(self, word):
        '''
        Return the position of '.' in a word. -1 denote there are no '.' appeared
        '''
        i = 0
        lenn = len(word)
        while i < lenn:
            if word[i] == '.' or word[i] == '!' or word[i] == '?' or word[i] == ';':
                return i
            i = i + 1

        return - 1
        
    def remove_double_star(self,line):
        '''
        Some auto - inserted patterns in discharge summaries
        '''
        pattern1 = r'\*\*NAME\[.{0,20}\]'
        tmp = re.sub(pattern1, '**NAME**', line)
        #pattern = r'\*\*(NAME\[.{0,20}\]|DATE\[.{0,20}\]|INSTITUTION|ID-NUM|AGE\[.{0,20}\][ ]{0,2}[a-zA-Z|-]+|PLACE|PHONE|ZIP-CODE|INITIALS|STREET-ADDRESS|PHONE|ROOM|WEB-LOC)'
        #tmp = re.sub(pattern, ' ', tmp)
        return tmp

    def prepare_text(self,text):
        '''
        Read text in to list,  remove the empty lines
        Parameters:
            text - string of text to be split
        Return:
            result - list of strings from text
        '''
        result = []
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 0:
                line = self.remove_double_star(line)
                line = self.clean(line)
                line = self.seperate_puncts(line)
                line = re.sub(r'[ ]+',' ',line)
                line = line.strip()
                if len(line) > 0: 
                    result.append(line)
        return result

    def seperate_puncts(self, line):
        '''
        seperate punctuations from words,  except '.'
        '''
        linee = ''
        for w in line:
            if self.is_punct(w):
                if len(linee) > 0 and linee[ -1] != ' ': 
                    linee = linee + ' ' +w + ' '
                else:
                    linee = linee + w + ' '
            else:
                linee = linee + w
        return linee.strip()

    def is_digit(self, word):
        '''
        Identify all numbers
        '''
        if re.match(r'[+-]?\d*[.]?\d+$', word): #all number
            return True
        return False

    def is_num_list(self, word):
        '''
        for list like:  1.   2.  
        '''
        if re.match(r'\d+\.$', word): #num list
            return True
        return False

    def is_punct(self, w):
        '''
        indentify the punctuation
        '''
#         if self.is_stop_punct(w):
#             return False
        if w == ',' or w == '?' or w == '!' or w == '"' or w == ';' or w == ':': 
            # '.' and '+' used in ABBR
            return True
        else:
            return False
        
    def clean(self, sentence):
        '''
        Clean text: replace '[ ]+' into '[ ]'; remove '^[ ]+' and '[ ]+$'
        '''
        sentence = re.sub(r'&amp;', '&', sentence)
        sentence = re.sub(r'&gt;|&gt[ ];|&lt;|&lt[ ];',' ', sentence)
        sentence = re.sub(r'\'s|\'S',' \'s',sentence)
        sentence = re.sub(r'[ ]+',' ',sentence)
        return sentence



    def get_ave_len(self, text):
        '''
        get the average length of all the lines
        '''
        lenn = len(text)
        avel = 0
        for line in text:
            avel = avel + len(line)
        return avel / lenn

    def is_stop_punct(self, w):
        '''
        These puncts are definitely a sentence boundary
        '''
        if w == '?' or w == '!' or w == '.' or w == ';': 
            return True
        else:
            return False
            
