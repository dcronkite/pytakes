import argparse

from pytakes.util import email_utils


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-s', '--subject', default='', help='Header for automated message.')
    parser.add_argument('-f', '--filename', default=None, help='Name of file to send.')
    parser.add_argument('-t', '--text', default=[], nargs='+', help='Text for email content.')
    parser.add_argument('-r', '--recipients', nargs='+', default=[], help='Recipients\' name,address.')
    parser.add_argument('--sender', default=None, help='Sender name,address.')
    parser.add_argument('--server-address', default=None, help='Mail server path.')
    args = parser.parse_args()
    email_utils.main(**vars(args))  # set up e-mail message and send


if __name__ == '__main__':  # if run from cmd line, not if imported
    main()
