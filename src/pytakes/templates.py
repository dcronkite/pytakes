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
{%- for meta_label in meta_labels %}
{{ meta_label }}
{%- endfor %}
--text-labels=note_text
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

PP_CONF_FILE = r'''--driver={{ driver }}
--server={{ server }}
--database={{ database }}
--input-table={{ destination_table }}_pre
--output-table={{ destination_table }}
--negation-table={{ negation_table }}
--negation-variation={{ negation_variation }}
--input-column=captured
--batch-count={{ batch_count }}
'''
