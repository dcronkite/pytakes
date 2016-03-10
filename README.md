## Requirements ##
* Python 3.3+
* regex package
* pyodbc package

## Prerequisites ##
1. Generate a word list of terms to find using dictionary builder script.
2. An input data table with the following columns (these can be altered on the automate_run script):
    * doc_id - unique for each piece of text
    + note_text - text of the notes themselves

## Doco ##

### Basics ###
Until I add more doco, check out the pytakes-automate-run script (should be in your Scripts directory). Run it with the `--create-sample` option to autogenerate a sample configuration file.


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
This is the table containing the terms you want to search for (i.e., the entities you wan't extracted). I have a script to auto-generate these, and will plan to include this in the file in due course (give me month ;) ). This is comparable to input required by cTAKES (and is derived from that).

    ​Column	​Type	​Description
    ​ID	​int	​identity column; unique integer for each row
    ​CUI	​varchar(8)	​category identifier; can be used to "group" different     terms together
    ​Fword	​varchar(80)	​first word of term
    ​Text	​varchar(8000)	​term
    ​Code	​varchar(45)	​unimportant value required by cTAKES (legacy)
    ​SourceType	​varchar(45)	​unimportant value required by cTAKES (legacy)
    ​TUI	​varchar(4)	​​unimportant value required by cTAKES (legacy)
    ​TextLength	​int	​length of term (all characters including spaces)
    ​RegexVariation	​int	​amount of variation: 0=none; 3=very; 1=default; see #Rules#parameters below; I suggest you just use "0"
    ​WordOrder	​int	​how accurate must the given word order be; 2=exactly; 1=fword constraint; 0=no word order
    Valence	​int	​this should just be "1"; pytakes not designed to work with this correctly


#### Document Table ####
This is the table containing the text you are in interesting in searching in.

The text itself must currently be labeled 'note_text'. The option to specify this is currently not implemented. Sorry.

The document table must also include a unique id for each note_text (just make an autoincrementing primary key). Specify this and any other meta information you want to pass along under '--meta-labels' option (ensure that the unique doc_id is specified first).


#### Example Config File ####
To get started, create the following file and then run:

    pytakes-automate-run --create-sample >> config
    # edit sample config file
    pytakes-automate-run @config

    # open the directory OUTPUT_DIRECTORY
    # run each auto-generated batch file

    # when all batch files have been run,
    # open the "post" directory, and run the
    # post process batch script


Config.conf:

    --server=MY_SERVER
    --database=MY_DB
    --dictionary-table=MY_DICTIONARY_TABLE
    --negation-table=MY_NEGATION_TABLE
    --negation-variation=0
    --document-table=MY_DOCUMENT_TABLE
    --meta-labels
    doc_id   # the first one must be a unique id per document
    date
    --text-labels   # not yet implemented, where your text goes, defaults to "note_text"
    note_text
    --output-dir=OUTPUT_DIRECTORY
    --destination-table=pytakes_out_20150217
    --max-intervening-terms=2
    --max-length-of-search=2
    --regex-variation=-1
    --mail-server-address=mail.my.org
    --sender
    Automated Notification,name.my@my.org
    --recipients
    My Name,name.my@my.org