"""Removing file content from the logic of automate run.

"""

RUN_BATCH_FILE = r'''@echo off
echo Running batch {{ batch_number }}.
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\processor.py "@.\pytakes-batch{{ batch_number }}.conf"
if %%errorlevel%% equ 0 (
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\ghri\email_utils.py -s "Batch {{ batch_number }} Completed" "@.\email.conf"
echo Successful.
) else (
python G:\CTRHS\NLP_Projects\Code\Source\pyTAKES\src\ghri\email_utils.py -s "Batch {{ batch_number }} Failed: Log Included" -f ".\log\pytakes-processor{{ batch_number }}.log" "@.\bad_email.conf"
echo Failed.
)
pause
'''

RUN_CONF_FILE = r'''--driver={{ driver }}
--server={{ server }}
--database={{ database }}
--document-table={{ document_table }}
--meta-labels
{%- for meta_label in meta_labels -%}
{{ meta_label }}
{%- endfor %}
--text-labels=note_text
--destination-table={{ destination_table }}_pre
{%- for option in options -%}
{{ option }}
{%- endfor %}
--batch-mode={{ primary_key }}
--batch-size={{ batch_size }}
--batch-number
{{ batch_start }}
{{ batch_end }}
'''