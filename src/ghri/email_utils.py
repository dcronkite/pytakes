'''
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
'''
# from std_import import *
import smtplib
import email.utils
import datetime
from email.mime.text import MIMEText
import argparse


# smtp server address
SERVER = 'mailhost.ghc.org'

# header information for sender
FROM = email.utils.formataddr(('Automated Notification', 'cronkite.d@ghc.org'))

# names of sendees, to be put in header
TONAMES = ['David']

# addresses of sendees, for header and envelope
TOADDYS = ['cronkite.d@ghc.org']

# header information for sendees
TO = email.utils.formataddr((','.join(TONAMES), ','.join(TOADDYS)))
SUBJECT = 'Automated Notification'     # subject of e-mail message
                            
def getTextFromFile(fn):
    '''
    Function: getTodaysLines
    Input: fn - filename to get lines from
    Output: answer - a list of the lines (with training newlines) in fn where
                     a string representing today's date in the format yyyy-mm-dd
                     is present
    Functionality: Get's the current day's lines out of a log file into a list
    '''
    with open(fn) as f:
        all = f.read()       # get all lines from file

    # convert today's date into string
#     todaystr = datetime.datetime.today().strftime('%Y-%m-%d')

    # filter all lines by those with today's date in them
#     answer = [line for line in alllines if todaystr in line]

    return all                       # return output


def resolveRecipients( recipients ):
    resRecipients = []
    resAddr = []
    for rec in recipients:
        if ',' in rec:
            name,addr = rec.split(',')
        else:
            name,addr = rec,rec
            
        resRecipients.append( email.utils.formataddr( (name, addr) ) )
        resAddr.append( addr )
    return resAddr, ';'.join( resRecipients )
        

def main(subject='',
         filename=None,
         text=[],
         recipients=[]):
    '''
    Function: main
    Input: none
    Output: none
    Functionality: Sets up e-mail message and sends
    '''
    if not isinstance(text, str):
        text = '\n'.join(text)
    
    if recipients:
        TOADDYS, TO = resolveRecipients( recipients )
    
    if filename:
        try:
            ftext = getTextFromFile(filename)
        except:
            ftext = 'Failed to retrieve text from file "%s".' % filename
    else:
        ftext = '' 

    # create the text of the body
    msgstring = '''This is an automated email.
    
    %s

    %s\n'''

    # create MIME message from message body
    msg = MIMEText(msgstring%(text, ftext))
    msg['From'] = FROM                  # set header from info
    msg['To'] = TO                      # set header to info
    msg['Subject'] = 'Automated Message: %s' % subject            # set header subject
    server = smtplib.SMTP(SERVER)       # open connection to smtp server
    server.sendmail(TOADDYS[0], TOADDYS, msg.as_string())   # send the e-mail

    return

if __name__ == '__main__':  # if run from cmd line, not if imported
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-s', '--subject', default='', help='Header for automated message.')
    parser.add_argument('-f','--filename',default=None, help='Name of file to send.')
    parser.add_argument('-t','--text',default=[], nargs='+', help='Text for email content.')
    parser.add_argument('-r', '--recipients', nargs='+', default=[], help='Recipients\' name,address.')
    args = parser.parse_args()
    main( **vars(args) )           # set up e-mail message and send