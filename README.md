# pytakes
Simple entity extraction module released under the MIT license.

## Overview

This module will look for a pre-defined set of terms in a corpus of text, and use a variation of the negex/context algorithm to determine whether these terms express negation, historical, or various other qualifiers. (The set of negation terms is also configurable.)

## Requirements ##
* Python 3.6+
* See requirements.txt (`pip install -r requirements.txt`)
    * Various requirements-_.txt files are provided depending on your needs:
        * dev: for running tests, general development
        * db: for connecting to database using pyodbc
        * psql: connecting to postgres database
        * sas: if data is stored in SAS
      

## Prerequisites ##
1. Generate a word list of terms/concepts ('concept dictionary')
    * in pyTAKES, a 'concept' is a set of terms with more or less the same meaning (e.g., ckd, chronic kidney disease)
    * the minimal should be a CSV file with three columns:
        * id - unique int for each line
        * cui - string label for a 'concept' ('concept unique identifier')
        * text - text to look for
    * dictionary builder script is also provided which help generate variations of terms(documented below)
2. A corpus with an id (for tracking, this will be in output) and text field (for processing, extracting concepts)

## Doco ##

### Basics ###

* The entry point is `python example/run.py config.py`. 
    * You can see an example `config.py` at `example/simple/example.config.py`
    * `pytakes` module must be on your PYTHONPATH, so `set/export PYTHONPATH=src` prior to running
        

### Install ###
1. Clone from git repo: `git clone ...pytakes.git`
2. `cd pytakes`
3. (optional) build virtualenv
    * `PYTHON_INSTALL/Scripts/virtualenv .venv`
    * `pip install virtualenv` if not yet available
4. Pip install prerequisites `pip install -r requirements.txt` 
5. Run tests (`pytest tests`)

### Use ###
You will need to have an input `concepts.csv` file with at least three columns (`id`, `cui`, `text`). There are several examples in the `pytakes/tests/data` directory.

#### Negation Table ####
This table implements a modified version of Chapman's ConText (see, e.g., http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.145.6566&rep=rep1&type=pdf, and https://code.google.com/archive/p/negex/).

This table is loosely based on the csv file here: https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/negex/lexical_kb.csv

Columns:

1. negex: negation (or related) term; capitalization and punctuation will be normalized (i.e., removed) so just include letters; I don't think regexes work
2. type: four letter abbreviation for negation role with brackets (these will vary based on your text and what you want to extract)
    * `[IMPR]`: improbable words (e.g., 'low probability')
    * `[NEGN]`: negation words (e.g., 'denies')
    * `[PSEU]`: pseudonegation (e.g., 'not only')
    * `[INDI]`: indication (e.g., 'rule out')
    * `[HIST]`: historical (e.g., 'previous')
    * `[CONJ]`: conjunction - interferes with negation scope (e.g., 'though', 'except')
    * `[PROB]`: probable (e.g., 'appears')
    * `[POSS]`: possible (e.g., 'possible')
    * `[HYPO]`: hypothetical (e.g., 'might')
    * `[OTHR]`: other subject - refers to someone other than the subject (e.g., 'mother')
    * `[SUBJ]`: subject - when reference of OTHR is still referring to the subject (e.g., 'by patient mother')
    * `[PREN]`: prenegation <- not sure if this is supposed to be used
    * `[AFFM]`: affirmed (e.g., 'obvious', 'positive for')
    * `[FUTP]`: future possibility (e.g., 'risk for')
3. direction
    * 0: directionality doesn't make sense (e.g., CONJ)
    * 1: term applies negation, etc. **backward** in the sentence (e.g., 'not seen')
    * 2: term applies negation, etc. **forward** in the sentence (e.g., 'dont see')
    * 3: term applies negation, etc. **forward and/or backward** in the sentence (e.g., 'likely')


#### Concept/Term Table ####
This is the table containing the terms you want to search for (i.e., the entities you want extracted). I have added a script to autogenerate these based on some basic configuration files.

    ​Column	​Type	​Description
    ​ID	​int	​identity column; unique integer for each row
    ​CUI	 string	​category identifier; can be used to "group" different     terms together
    ​Text	​string	​term
    ​RegexVariation	​int	​amount of variation: 0=none; 3=very; 1=default; -1=don't even allow suffixes, exact matches only; see #Rules#parameters below; I suggest you just use "0" or "-1"
    ​WordOrder	​int	​how accurate must the given word order be; 2=exactly; 1=fword constraint; 0=no word order
    MaxIntervening	int	how many intervening words to allow when locating words; 'how many intervening words do I allow?'
    MaxWords	int	how many words to look ahead to find the next word; is ‘how far do I look ahead after each term?’ 
    
MaxIntervening and MaxWords should not be used together.
    
To autogenerate this table format, use the `pytakes-build-dictionary` script installed into the Python Scripts directory. For an example, run this with the `--create-sample` option (optionally specify the output with the `--path C:\somewhere` option. For additional specifications, see the "Dictionary Builder" section below.


#### Document Table ####
This is the table containing the text you are in interesting in searching in.

The text itself must currently be labeled 'note_text'. The option to specify this is currently not implemented. Sorry.

The document table must also include a unique id for each note_text (just make an autoincrementing primary key). Specify this and any other meta information you want to pass along under `--meta-labels` option (**ensure that the unique doc_id is specified first**).


#### Example Config File ####
I prefer to specify the configuration file as a Python file (`config.py`). Yaml and json are also accepted. See an example below (copied from `example.config.py`). Please note that the `print(config`) at the end is required.

    config = {
        'corpus': {  # how to get the text data
            'directories': [  # specify path to .txt files
                r'PATH'
            ],
            'connections': [  # specify other connection types
                {
                    'name': 'TABLENAME',
                    'name_col': 'TEXT ID COLUMN',
                    'text_col': 'TEXT COLUMN',
                    # specify either driver/server/database OR connection_string
                    # connection string examples here: https://docs.sqlalchemy.org/en/13/core/engines.html
                    'connection_string': 'SQLALCHEMY-LIKE CONNECTION_STRING',
                    # db args: driver/server/database
                    'driver': 'DRIVER',  # available listed in pytakes/iolib/sqlai.py, or use connection string
                    'server': 'SERVER',
                    'database': 'DATABASE',
                }
            ]
        },
        'keywords': [  # path to keyword files, usually stored as CSV
            {
                'path': r'PATH',
                'regex_variation': 0  # set to -1 if you don't want any expansion
            }
        ],
        'negation': {  # select either version or path (not both)
            'path': r'PATH TO NEGATION CSV FILE',
            'version': 1,  # int (version number), built-in/default
            'skip': False,  # bool: if skip is True: don't do negation
        },
        'output': {
            'path': r'PATH TO OUTPUT DIRECTORY',
            'outfile': 'NAME.out.jsonl',  # name of output file (or given default name)
            'hostname': ''
        },
    }
    
    print(config)

    
## Dictionary Builder ###
For a simple example, run (you will first need to install this package, run `python setup.py install` in the base directory): 

    pytakes-build-dictionary --create-sample --path OUTPUT_PATH
    
### COMMAND LINE ARGUMENTS ###
 
    Short​	​Long	​Description
    ​-p	​--path	​Specifies parent directory of folders; program will prompt if unable to locate the directory
    ​-o	​--output	​Specify output CSV file; if ".csv" is not included, it will be added
    ​-t	​--table	​Specify output table in specified database (See below)
    ​-v	​--verbosity	​Specify amount of log output to show: 3-most verbose; 0-least verbose
    --driver	If -t is specified, driver where table should be created. Defaults to SQL Server
    --server	If -t is specified, server where table should be created. 
    --database	If -t is specified, database where table should be created. 
   

###  OUTPUT COLUMNS ####
Not all of these output columns are required (most don't do anything). This was originally designed for building a dictionary using cTAKES.

     Column	​Type	​Description
     ID	​int	​identity column; unique integer for each row
     CUI	​varchar(8)	​category identifier; can be used to "group" different terms together
     Fword	​varchar(80)	​first word of term
     Text	​varchar(8000)	​term
     Code	​varchar(45)	​unimportant value required by cTAKES (legacy)
     SourceType	​varchar(45)	​unimportant value required by cTAKES (legacy)
     TUI	​varchar(4)	​​unimportant value required by cTAKES (legacy)
     TextLength	​int	​length of term (all characters including spaces)
     RegexVariation	​int	​amount of variation: 0=none; 3=very; 1=default; see #Rules#parameters below
     WordOrder	​int	​how accurate must the given word order be; 2=exactly; 1=fword constraint; 0=no word order
     Valence	​int	​this should just be "1"; program is  not designed to work with this correctly


### RULES ###
Rules are the text entries in the cTAKES-like dictionary, however, they can include "categories" in addition to just text.A category is any string of text surrounded by "[" and "]". The intervening text string is the name of a "category". The category must have a definition, and each item (synonym) in the definition will be used in the rule.

For example, if a rule is `[smart_person] is smart` and the category `smart_person` is defined by the terms "Albert Einstein", "Old McDonald", and "Brain", then the resulting output will be

    Albert Einsten is smart
    Old McDonald is smart
    Brain is smart
 

The rule file consists of a set of rules (as above), and each rule must be on its own line.

    [smart_person] is smart
    smart [smart_person]
    [smart_person] not dumb
    [not_so_smart] not smart 

The rule file must be named "rules" or "rules.some-extension" (e.g., "rules.txt"). 

####  Parameters ####
Rules may also maintain configuration parameters.The configurations are indexed in the following order (bold indicates the default parameter):

RegexVariation (integers)

    **0: no variation in regular expression coverage**
    1: minimal variation in regular expression coverage
    2: moderate variation in regular expression coverage
    3: high flexibility in regular expression coverage
    
WordOrder

    0: free word order
    **1: enforce first word rule**
    2: require precise word order
    
Valence

    **ALWAYS USE 1** or just ignore; NOT YET CORRECTLY IMPLEMENTED IN LCTAKES
    
These are designated by the double percent ('%%') and follow the rule. 

    [category]%%REGEX_VARIATION,WORD_ORDER,VALENCE

For example:

    [smart_person] is smart%%1,2   # minimal regex variation; requires precise word order 
    [smart_person]%%,2        # same as above: the first parameter is left blank, and the default is used
    [smart_person] not dumb           # default for both parameters are used
    [not_so_smart] not smart%%2    # default second parameter

 

 Definitions/categories (see below) can also be assigned parameters in exactly the same way. When the parameters collide/disagree (e.g., the rule asks for free word order, but the definition asks that the first word rule be enforced), the more conservative will be selected.

####  DEFINITIONS ####
The definition (also called "category" files) provide a set of words to replace the name of a category in a particular rule.The definition file must either be within a "cat" directory, or must have the extension ".cat". The program will choose one or the other--which one is undefined.There are several ways to write the definition for a particular category. Examples:

In the definition file smart_person.cat, each row will be considered a definition for the smart_person category. Also a not_so_smart.cat should be included.
In the definition file definitions.cat:

    [smart_person]                       
    Albert Einstein                       
    Old McDonald                       
    Brain                       
    [not_so_smart]                       
    Humpty Dumpty  

####  Comments. ####
All lines beginning with "#" are ignored, and all characters occurring after a '#' are ignored as comments.     
                  
    # last updated by me, yesterday evening                       
    [smart_person]                       
    Albert Einstein       # comment here                       
    Old McDonald                       
    Brain                       
    [not_so_smart]                       
    # shouldn't there be others?!?                       
    Humpty Dumpty  

####  CUIs. ####
CUIs are usually assigned uniquely for each rule, rather than for a category. A CUI can be included for a given definition of a category by assigning it with the syntax: C1025459==Albert Einstein
Or, in the entire definition file:

    [smart_person]                       
    C1025459==Albert Einstein                       
    C4495545==Old McDonald                       
    Brain                       
    [not_so_smart]                       
    Humpty Dumpty   

In the above example, Humpty Dumpty and Brain are both assigned a default CUI. 

####  Word Variant Notation. ####
Definitions may also be written on a single line, separated by the double pipe (i.e., '||'). If more than three or four definitions are listed on a single line, the definitions file becomes somewhat unreadable. Thus, it is best practice to only include word variants on a single line.                       

    [smart_person]                       
    C1025459==Albert Einstein||Einstein                       
    C4495545==Old McDonald||Ol' McDonald||Ole McDonald||Jeff                       
    Brain                       
    [not_so_smart]                       
    Humpty Dumpty||Humpty-Dumpty # this is a common use for word-variant notation   

#### Parameters ####
For definitions, see the parameters section under Rules.

Example:

    [smart_person]                       
    C1025459==Albert Einstein%%1,2   # all rules involving this definition with have minimal regex variation; requires precise word order                       
    C4495545==Old McDonald                       
    Brain                       
    [not_so_smart]                       
    Humpty Dumpty              # will use the defaults

 

**Conflict Resolution.**

Regardless of how the conflict occurs, the more conservative of the rule and all relevant definitions will be chosen. NB: This process will never choose values that have been left as default (unless the default is specifically requested).
