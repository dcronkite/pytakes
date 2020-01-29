"""Removing file content from the logic of automate run.

"""

# automate run details
RUN_BATCH_FILE = r'''@echo off
echo Running batch {{ batch_number }}.
{{ python }} {{ pytakes_path }}processor.py "@.\pytakes-batch{{ batch_number }}.conf"
if %%errorlevel%% equ 0 (
{% if send_email %}
{{ python }} {{ pytakes_path }}sendmail.py -s "Batch {{ batch_number }} Completed" "@.\email.conf"
{% endif %}
echo Successful.
) else (
{% if send_email %}
{{ python }} {{ pytakes_path }}sendmail.py -s "Batch {{ batch_number }} Failed: Log Included" -f ".\log\pytakes-processor{{ batch_number }}.log" "@.\bad_email.conf"
{% endif %}
echo Failed.
)
pause
'''

RUN_COMMAND_BATCH_FILE = r'''@echo off
echo Running batch {{ batch_number }}.
pytakes-processor "@.\pytakes-batch{{ batch_number }}.conf"
if %%errorlevel%% equ 0 (
{% if send_email %}
pytakes-sendmail -s "Batch {{ batch_number }} Completed" "@.\email.conf"
{% endif %}
echo Successful.
) else (
{% if send_email %}
pytakes-sendmail -s "Batch {{ batch_number }} Failed: Log Included" -f ".\log\pytakes-processor{{ batch_number }}.log" "@.\bad_email.conf"
{% endif %}
echo Failed.
)
pause
'''

RUN_CONF_FILE = r'''--driver={{ driver }}
--server={{ server }}
--database={{ database }}
--document-table={{ document_table }}
--meta-labels
{{ primary_key }}
{%- for meta_label in meta_labels %}
{{ meta_label }}
{%- endfor %}
--text-labels
{%- for text_label in text_labels %}
{{ text_label }}
{%- endfor %}
--tracking-method={{ tracking_method }}
--destination-table={{ destination_table }}_pre
{%- for option in options %}
{{ option }}
{%- endfor %}
--batch-mode={{ primary_key }}
--batch-size={{ batch_size }}
--batch-number
{{ batch_start }}
{{ batch_end }}
'''

EMAIL_CONF_FILE = r'''{% for recipient in recipients %}--recipient
{{ recipient }}
{%- endfor %}
--server-address={{ mail_server_address }}
--sender
{{ sender }}
--text
This notification is to inform you that another batch ({{ filecount }} total) has been completed for table {{ destination_table }}.
'''

BAD_EMAIL_CONF_FILE = r'''{%- for recipient in recipients %}--recipient
{{ recipient }}
{%- endfor %}
--server-address={{ mail_server_address }}
--sender
{{ sender }}
--text
This notification is to inform you that a batch ({{ filecount }} total) has failed for table {{ destination_table }}.

The log file is attached for debugging.
'''

PP_BATCH_FILE = r'''{{ python }} {{ pytakes_path }}postprocessor.py "@.\postprocess.conf"
pause
'''

PP_COMMAND_BATCH_FILE = r'''pytakes-postprocessor "@.\postprocess.conf"
pause
'''

PP_CONF_FILE = r'''--driver={{ driver }}
--server={{ server }}
--database={{ database }}
--input-table={{ destination_table }}_pre
--output-table={{ destination_table }}
{%- if negation_table and negation_variation %}
--negation-table={{ negation_table }}
--negation-variation={{ negation_variation }}
{% elif negation_table %}
--negation-table={{ negation_table }}
--negation-variation=-1
{%- endif %}
--input-column=captured
--batch-count={{ batch_count }}
--tracking-method={{ tracking_method }}
'''

SAMPLE_CONF_FILE = r'''--driver=DRIVER
--server=SERVER
--database=DB
--dictionary-table=DICTIONARY_TABLE
--negation-table=NEGATION_TABLE
--negation-variation=0
--document-table=DOCUMENT_TABLE
--output-dir=DIRECTORY
--destination-table=DESTINATION_TABLE
--max-intervening-terms=0
--max-length-of-search=1
--meta-labels
doc_id
pat_id
date
--primary-key
doc_id
--text-labels
note_text
--mail-server-address
mail.test.org
--sender
Automated Email,example@example.com
--recipients
Recipient Name,example@example.com
Recipient2 Name,example2@example.com
'''

# for processor.py
PROC_INSERT_INTO2_QUERY = r'''INSERT INTO {{ destination_table }} (
{%- for label in labels %}
{{ label }}{% if not loop.last %},{% endif %}
{%- endfor %}
) VALUES (
{%- for meta in metas %}
'{{ meta|replace("'", "''") }}',
{%- endfor %}
{{ feature.id() }},
'{{ captured|replace("'", "''") }}',
'{{ context|replace("'", "''") }}',
'{{ text|replace("'", "''") }}',
{{ feature.get_certainty() }},
{% if feature.is_hypothetical() %}1{% else %}0{% endif %},
{% if feature.is_historical() %}1{% else %}0{% endif %},
{% if feature.is_hypothetical() %}1{% else %}0{% endif %},
{{ feature.begin() }},
{{ feature.end() }},
{{ feature.get_absolute_begin() }},
{{ feature.get_absolute_end() }}
{% if hostname %}, '{{ hostname|replace("'", "''") }}', {{ batch_number }}{% endif %}
)
'''

PROC_INSERT_INTO3_QUERY = r'''INSERT INTO {{ destination_table }} (
{%- for label in labels %}
{{ label }}{% if not loop.last %},{% endif %}
{%- endfor %}
) VALUES (
{%- for meta in metas %}
'{{ meta }}',
{%- endfor %}
{{ feature.get_id() }},
{{ feature.get_feature() }},
{{ feature.get_category() }}
{% if hostname %}, {{ hostname }}, {{ batch_number }}{% endif %}
)
'''

PROC_GET_DOC_IDS = r'''SELECT {{ table_id }}
FROM {{ doc_table }}
{%- if order_by %}
ORDER BY {{ order_by }}
{%- endif %}
'''

PROC_CREATE_TABLE = r'''CREATE TABLE {{ destination_table }} (
rowid int IDENTITY(1, 1) PRIMARY KEY,
{%- for label, column_type in labels_types %}
{{ label }} {{ column_type }}{% if not loop.last %},{% endif %}
{%- endfor %}
)
'''

PROC_GET_CONTEXT = r'''SELECT negex, type, direction
FROM {{ neg_table }}
'''

PROC_GET_TERMS = r'''SELECT id
    , text
    , cui
    ,{% if 'valence' not in columns %}  {% if valence %} {{ valence }} {% else %} 1 {% endif %}  as {% endif %} valence
    ,{% if 'regexvariation' not in columns %} {% if regex_variation %} {{ regex_variation }} {% else %} 3 {% endif %} as {% endif %} regexvariation
    ,{% if 'WordOrder' not in columns %} {% if word_order %} {{ word_order }} {% else %} 1 {% endif %} as {% endif %}  wordorder
FROM {{ term_table }}
'''

PROC_GET_DOCS = r'''SELECT
{%- if where_clause and order_by %}
TOP {{ batch_size }}
{%- endif %}
{%- for meta in meta_labels %}
{{ meta }},
{%- endfor %}
{%- for text in text_labels %}
{{ text }}{% if not loop.last %},{% endif %}
{%- endfor %}
FROM {{ doc_table }}
{%- if where_clause and order_by %}
WHERE {{ where_clause }}
ORDER BY {{ order_by }}
{%- endif %}
'''

# for postprocessor.py
PP_INSERT_INTO = r'''INSERT INTO {{ table_name }} (
{%- for label in labels %}
{{ label }} {% if not loop.last %},{% endif %}
{%- endfor %}
) VALUES (
{%- for value in values %}
    {%- if value is number %}
    {{ value }}
    {%- else %}
    '{{ value|replace("'", "''") }}'
    {%- endif %}
     {% if not loop.last %},{% endif %}
{%- endfor %}
)
'''

PP_INPUT_DATA = r'''SELECT
{%- for label in labels %}
{{ label }} {% if not loop.last %},{% endif %}
{%- endfor %}
FROM {{ input_table }}
'''

PP_PREP_DEST_TABLE = r'''ALTER TABLE {{ table_name }}
ADD updated int
'''

PP_DEST_TABLE = r'''SELECT *
INTO {{ dest_table }}
FROM {{ input_table }}
WHERE 1 = 2
'''