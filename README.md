## Requirements ##
Python 3.3+
regex package
pyodbc package

## Prerequisites ##
1. Generate a word list of terms to find using dictionary builder script.
2. An input data table with the following columns (these can be altered on the automate_run script):
    * Ft_id - unique for each piece of text
    * hybrid_date - date
    + note_text - text of the notes themselves

## Use ##
Until I add more doco, check out the automate_run.py script (should be in your Scripts directory).

Right now, you will need to create two additional tables in the specified server/database with these names/columns:
1. res_ss_word: word
2. res_ss_abbr: abbr
These had something to do with sentence splitting (don't split the abbreviations, but not sure about the words).