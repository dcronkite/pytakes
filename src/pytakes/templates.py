"""Removing file content from the logic of automate run.

"""

RUN_BATCH_FILE = r'''@echo off
echo Running batch {{ batch_number }}.
{{ python }} {{ pytakes_path }}processor.py "@.\pytakes-batch{{ batch_number }}.conf"
if %%errorlevel%% equ 0 (
{{ python }} {{ pytakes_path }}sendmail.py -s "Batch {{ batch_number }} Completed" "@.\email.conf"
echo Successful.
) else (
{{ python }} {{ pytakes_path }}sendmail.py -s "Batch {{ batch_number }} Failed: Log Included" -f ".\log\pytakes-processor{{ batch_number }}.log" "@.\bad_email.conf"
echo Failed.
)
pause
'''

RUN_COMMAND_BATCH_FILE = r'''@echo off
echo Running batch {{ batch_number }}.
pytakes-processor "@.\pytakes-batch{{ batch_number }}.conf"
if %%errorlevel%% equ 0 (
pytakes-sendmail -s "Batch {{ batch_number }} Completed" "@.\email.conf"
echo Successful.
) else (
pytakes-sendmail -s "Batch {{ batch_number }} Failed: Log Included" -f ".\log\pytakes-processor{{ batch_number }}.log" "@.\bad_email.conf"
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
--text-labels=note_text
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

EMAIL_CONF_FILE = r'''{%- for recipient in recipients %}--recipient
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
--negation-table={{ negation_table }}
--negation-variation={{ negation_variation }}
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
--sender
Automated Email,example@example.com
--recipients
Recipient Name,example@example.com
Recipient2 Name,example2@example.com
'''

INSERT_INTO2_QUERY = r'''INSERT INTO {{ destination_table }} (
{%- for label in labels %}
{{ label }}{% if not loop.last %},{% endif %}
{%- endfor %}
) VALUES (
{%- for meta in metas %}
'{{ meta }}',
{%- endfor %}
{{ feature.id() }},
'{{ captured }}',
'{{ context }}',
'{{ text }}',
{{ feature.get_certainty() }},
{% if feature.is_hypothetical() %}1{% else %}0{% endif %},
{% if feature.is_historical() %}1{% else %}0{% endif %},
{% if feature.is_hypothetical() %}1{% else %}0{% endif %},
{{ feature.begin() }},
{{ feature.end() }},
{{ feature.get_absolute_begin() }},
{{ feature.get_absolute_end() }}
{% if hostname %}, {{ hostname }}, {{ batch_number }}{% endif %}
)
'''

INSERT_INTO3_QUERY = r'''INSERT INTO {{ destination_table }} (
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
