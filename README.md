## Requirements ##
* Python 3.3+
* regex package
* pyodbc package

## Prerequisites ##
1. Generate a word list of terms to find using dictionary builder script.
2. An input data table with the following columns (these can be altered on the automate_run script):
    * Ft_id - unique for each piece of text
    * hybrid_date - date
    + note_text - text of the notes themselves

## Doco ##

### Basics ###
Until I add more doco, check out the automate_run.py script (should be in your Scripts directory).

Right now, you will need to create two additional tables in the specified server/database with these names/columns:

1. res_ss_word: word
2. res_ss_abbr: abbr

These had something to do with sentence splitting (don't split the abbreviations, but not sure about the words).

### Install ###
1. Clone from bitbucket repo.
2. Run python setup.py install

### Use ###
You will need a few different input tables.

#### Negation Table ####
This table implements a modified version of Chapman's ConText (see, e.g., http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.145.6566&rep=rep1&type=pdf, and https://code.google.com/archive/p/negex/).

This table is loosely based on the csv file here: https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/negex/lexical_kb.csv

Columns:

1. negex: negation (or related) term; capitalization and punctuation will be normalized (i.e., removed) so just include letters; I don't think regexes work
2. type: four letter abbreviation for negation role with brackets (these will vary based on your text and what you want to extract)
    * [IMPR]: improbable words (e.g., 'low probability')
    * [NEGN]: negation words (e.g., 'denies')
    * [PSEU]: pseudonegation (e.g., 'not only')
    * [INDI]: indication (e.g., 'rule out')
    * [HIST]: historical (e.g., 'previous')
    * [CONJ]: conjunction - interferes with negation scope (e.g., 'though', 'except')
    * [PROB]: probable (e.g., 'appears')
    * [POSS]: possible (e.g., 'possible')
    * [HYPO]: hypothetical (e.g., 'might')
    * [OTHR]: other subject - refers to someone other than the subject (e.g., 'mother')
    * [SUBJ]: subject - when reference of OTHR is still referring to the subject (e.g., 'by patient mother')
    * [PREN]: prenegation <- not sure if this is supposed to be used
    * [AFFM]: affirmed (e.g., 'obvious', 'positive for')
    * [FUTP]: future possibility (e.g., 'risk for')
3. direction
    * 0: directionality doesn't make sense (e.g., CONJ)
    * 1: term applies negation, etc. **backward** in the sentence (e.g., 'not seen')
    * 2: term applies negation, etc. **forward** in the sentence (e.g., 'dont see')
    * 3: term applies negation, etc. **forward and/or backward** in the sentence (e.g., 'likely')


#### Term Table #### 
This is the table containing the terms you want to search for (i.e., the entities you wan't extracted.


#### Document Table ####
This is the table containing the text you are in interesting in searching in.


#### Example Config File ####
To get started, create the following file and then run:

    pytakes-automate-run @config.conf

Config.conf:

    --server=MY_SERVER
    --database=MY_DB
    --dictionary-table=MY_DICTIONARY_TABLE
    --negation-table=MY_NEGATION_TABLE
    --negation-variation=0
    --document-table=MY_DOCUMENT_TABLE
    --meta-labels
    doc_id
    date
    note_text
    --output-dir=main
    --destination-table=pytakes_out_20150217
    --max-intervening-terms=2
    --max-length-of-search=2
    --regex-variation=-1
    --mail-server-address=mail.my.org
    --sender
    Automated Notification,name.my@my.org
    --recipients
    My Name,name.my@my.org