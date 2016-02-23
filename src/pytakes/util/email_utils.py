"""
File: email_vmmc_log.py
Author: Scott Halgrim, halgrim.s@ghc.org
Date: 6/3/13
Functionality: Sends the latest info from the vmmc log so its status can
               more easily be checked.
Contents:
    LOGFN - log filename of delining process to send results from
    SERVER - smtp server address
    FROM - header info for sender
    TONAMES - list of names of sendees for header
    TOADDYS - list of e-mail addys for header and envelope
    TO - header info for sendees
    SUBJECT - subject of e-mail message
    getTodaysLines - function that get's the current day's lines out of a log
                     file into a list
    main - function that sets up the e-mail message with the appropriate message
           and sends
    __main__ code that calls main
TODO:
    - Make this more sophisticated
      - Store the last line sent and then use that to just get all the new lines
      - There may even be an SMTP handler in the logging stuff
NOTES:
    - Just copied from email_delining_log.py to create
"""
import logging
import smtplib
import email.utils
from email.mime.text import MIMEText
import argparse


def get_text_from_file(fn):
    """
    Function: getTodaysLines
    Input: fn - filename to get lines from
    Output: answer - a list of the lines (with training newlines) in fn where
                     a string representing today's date in the format yyyy-mm-dd
                     is present
    Functionality: Get's the current day's lines out of a log file into a list
    """
    with open(fn) as f:
        all_ = f.read()  # get all lines from file
    return all_  # return output


def resolve_recipients(recipients):
    resrecipients = []
    resaddr = []
    for rec in recipients:
        if ',' in rec:
            name, addr = rec.split(',')
        else:
            name, addr = rec, rec

        resrecipients.append(email.utils.formataddr((name, addr)))
        resaddr.append(addr)
    return resaddr, ';'.join(resrecipients)


def main(subject='', filename=None, text='',
         recipients=None, sender=None, server_address=None):
    """
    Functionality: Sets up e-mail message and sends

    :param subject:
    :param filename:
    :param recipients: list of string of "name,email@address"
    :param text:
    :param sender: string of "name,email@address"
    :param server_address: string
    """
    if not isinstance(text, str):
        text = '\n'.join(text)

    toaddys, to_ = resolve_recipients(recipients)

    _, from_ = resolve_recipients([sender])

    if filename:
        try:
            ftext = get_text_from_file(filename)
        except Exception as e:
            ftext = 'Failed to retrieve text from file "{}". {}'.format(filename, e)
    else:
        ftext = ''

        # create the text of the body
    msgstring = '''This is an automated email.
    
    %s

    %s\n'''

    # create MIME message from message body
    msg = MIMEText(msgstring % (text, ftext))
    msg['From'] = from_  # set header from info
    msg['To'] = to_  # set header to info
    msg['Subject'] = 'Automated Message: %s' % subject  # set header subject
    server = smtplib.SMTP(server_address)  # open connection to smtp server
    server.sendmail(toaddys[0], toaddys, msg.as_string())  # send the e-mail

    return


if __name__ == '__main__':  # if run from cmd line, not if imported
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-s', '--subject', default='', help='Header for automated message.')
    parser.add_argument('-f', '--filename', default=None, help='Name of file to send.')
    parser.add_argument('-t', '--text', default=[], nargs='+', help='Text for email content.')
    parser.add_argument('-r', '--recipients', nargs='+', default=[], help='Recipients name,address.')
    parser.add_argument('--sender', default=None, help='Sender name,address.')
    parser.add_argument('--server-address', default=None, help='Mail server path.')
    args = parser.parse_args()
    main(**vars(args))  # set up e-mail message and send
