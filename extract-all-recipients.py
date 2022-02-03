"""Create a connection to Gmail and do something with the results

PURPOSE
writes out all the email addresses for all recipient types in a mailbox for the specified date range

USAGE
Run this program with -h

WARNING
1. This program accepts your password as a command line argument. Some will NOT like this.

References:
http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/
and
https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/

this code from original author _abought_
https://gist.github.com/abought/15a1e08705b121c1b7bd


"""

import argparse
import csv
import imaplib
import getpass
import string
import sys
import ssl

from pprint import pprint as pp

import email.parser
import email.utils
from email.utils import parsedate_to_datetime

import datetime
from datetime import date
import dateutil.relativedelta

import logging
from loggingconfig import load_logging

load_logging()
logger = logging.getLogger(__name__)

# argparse and IMAP search formats
# YYYY-MM-DD - 2021-01-30
date_format_input = "%Y-%m-%d"
# DD-Mon-YYYY 31-Jan-2021
date_format_filter = "%d-%b-%Y"

# User may want to change these parameters if running script as-is
IMAP_SERVER_DEFAULT = "imap.gmail.com"
# Search folders, multiple directories can be given
# TODO: A user will want to change this
SEARCH_FOLDER = ["[Gmail]/Trash", "[Gmail]/All Mail", "INBOX"]

# dictionary and dataframe labels
label_message_id = "Message-ID"
label_message_date = "Date"
label_folder = "Folder"
label_message_subject = "Subject"
label_recipients = "Recipients"
label_from = "From"
label_to = "To"
label_cc = "Cc"
label_bcc = "Bcc"
label_reply_to = "Reply-To"
label_sender = "Sender"
# fields that contain mail addresses
addr_fields = [label_from, label_to, label_cc, label_bcc, label_reply_to, label_sender]
output_fields = [
    label_message_date,
    label_folder,
    label_message_id,
    label_message_subject,
    label_recipients,
    label_from,
    label_to,
    label_cc,
    label_bcc,
    label_reply_to,
    label_sender,
]


def connect(username, password, server):
    """Connect to [the specified] mail server. Return an open connection"""
    conn = imaplib.IMAP4_SSL(host=server, ssl_context=ssl.create_default_context())
    logger.info("Connection welcom: %s", conn.welcome)
    try:
        resp, data = conn.login(username, password)
        logger.info("Login returned: %s", resp)
    except imaplib.IMAP4.error:
        logger.error("Failed to login ")
        sys.exit(1)
    return conn


def log_folders(conn):
    """logs a list of open mailbox folders"""
    for f in conn.list():
        for i in f:
            logger.info("    %s", i)


def get_mails_from_folder(conn, folder_name, start_date, before_date):
    """Fetch a specific folder (or label) from server"""
    # wrap in double quotes in case there are / or spaces
    typ, data = conn.select(mailbox='"%s"' % folder_name, readonly=True)
    if typ != "OK":
        logger.info("Could not open specific folder")
        log_folders(conn)
        return

    search_string = "ALL"
    search_string = '(since "%s" before "%s")' % (
        start_date.strftime(date_format_filter),
        before_date.strftime(date_format_filter),
    )

    typ, data = conn.search(None, search_string)
    if typ != "OK":
        logger.warn("Could not get mail list of folder: %s", folder_name)
        return

    return data[0].split()


def fetch_message(conn, msg_uid):
    """
    Fetch a specific message uid (not sequential id!) from the given folder;
    return the parsed message. User must ensure that specified
    message ID exists in that folder.
    """
    # TODO: Could we fetch just the envelope of the response to save bandwidth?
    typ, data = conn.fetch(msg_uid, "(RFC822)")
    if typ != "OK":
        logger.error("ERROR fetching message #%s", msg_uid)
        return

    return email.parser.BytesParser().parsebytes(data[0][1], headersonly=True)


def get_summary_from_message(msg, folder_name):
    """Given a parsed message, extract a dictionary with interesting fields"""
    message_definition = {}

    # store message identifiers
    message_definition[label_message_date] = parsedate_to_datetime(
        msg[label_message_date]
    ).strftime("%Y-%m-%d %H:%M:%S")
    message_definition[label_folder] = folder_name
    message_definition[label_message_id] = msg[label_message_id]
    message_definition[label_message_subject] = msg[label_message_subject]
    message_definition[label_recipients] = []

    for f in addr_fields:
        # wish we had TRACE
        # logger.debug("Examining Message %s", msg)
        # set it to empty in case the recipient type wasn't in the message
        message_definition[f] = []
        if msg[f] is not None:
            logger.debug("%s exists as %s", f, msg[f])
            address_tuples = email.utils.getaddresses(msg.get_all(f, []))
            # convert all to lower case for easier matching
            rlist = [x[1].lower() for x in address_tuples]
            logger.debug("getaddress: %s", rlist)
            message_definition[f] = rlist
            if rlist is not None:
                logger.debug(
                    "appending %s to %s", rlist, message_definition[label_recipients]
                )
                for address in rlist:
                    message_definition[label_recipients].append(address)

    if not message_definition[label_recipients]:
        logger.error("Error no people attached to def %s", message_definition)
        logger.error("Error no people attached to msg %s", msg)
        exit()
    return message_definition


def get_recipients_from_folder(mail_conn, folder_name, start_date, before_date):
    """Read each message in a mailbox, write to CSV with folder name"""
    logger.info("Looking at folder %s", folder_name)

    folder_recipients = []
    mails = get_mails_from_folder(mail_conn, folder_name, start_date, before_date)
    # convert special characters to underscores - to support GMAIL standard names
    file_name = folder_name.translate(
        {ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-= +"}
    )
    with open(file_name + ".csv", "w") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=output_fields, restval="0")
        writer.writeheader()
        if mails is not None:
            for mail_id in mails:
                data = fetch_message(mail_conn, mail_id)
                message_summary = get_summary_from_message(
                    msg=data, folder_name=folder_name
                )
                logger.debug("%s", message_summary)
                writer.writerow(message_summary)
                folder_recipients.extend(message_summary[label_recipients])
            logger.info("Processed %s from %s", len(mails), folder_name)
        csvfile.close()

    return folder_recipients


def main():
    # set these as the default and feed them to argparse
    # pick dates before today because means we get same results in today's runs
    start_date = date.today() - dateutil.relativedelta.relativedelta(weeks=1)
    before_date = date.today()
    # create formated strings for argparse
    start_date_as_input = start_date.strftime(date_format_input)
    before_date_as_input = before_date.strftime(date_format_input)

    # convert input style string to date time
    start_date = datetime.datetime.strptime("2020-01-01", date_format_input)
    before_date = datetime.datetime.strptime("2020-02-01", date_format_input)

    parser = argparse.ArgumentParser(
        description="Retrieve recipients from matching mailboxes and date range and write to csv files."
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        required=True,
        help="the email username not optional",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        required=True,
        help="the email password not optional",
    )
    # make this optional because we want to list out the folders if not provided
    parser.add_argument(
        "-if",
        "--imap-folder",
        dest="folder",
        type=str,
        required=False,
        action="append",
        help="the folder we wish to scan",
    )
    parser.add_argument(
        "-sd",
        "--start-date",
        dest="start_date",
        type=lambda d: datetime.datetime.strptime(d, date_format_input).date(),
        default=start_date_as_input,
        required=False,
        help="start date Default: " + start_date_as_input,
    )
    parser.add_argument(
        "-bd",
        "--before-date",
        dest="before_date",
        type=lambda d: datetime.datetime.strptime(d, date_format_input).date(),
        default=before_date_as_input,
        required=False,
        help="prior to date Default: " + before_date_as_input,
    )

    parser.add_argument(
        "--imap-server",
        dest="imap_server",
        type=str,
        default=IMAP_SERVER_DEFAULT,
        required=False,
        help="imap server Default: " + IMAP_SERVER_DEFAULT,
    )

    parser.add_argument(
        "-oud",
        "--unique-domains",
        action="store_true",
        dest="unique_domains",
        help="output is unique domains",
    )

    parser.add_argument(
        "-oad",
        "--all-addresses",
        action="store_true",
        dest="all_addresses",
        help="output is all addresses",
    )

    parser.add_argument(
        "-oua",
        "--unique-addresses",
        action="store_true",
        dest="unique_addresses",
        help="output is unique addresses",
    )

    args = parser.parse_args()
    username = args.username
    password = args.password
    mail_server = args.imap_server
    before_date = args.before_date
    start_date = args.start_date

    # Connect
    mail_conn = connect(username=username, password=password, server=mail_server)

    if args.folder is None:
        # show folders of mail account
        log_folders(mail_conn)
        logger.error(
            "Must specify one of the folders above using --folder : Ex: --folder INBOX"
        )
        exit()

    # leave legacy code for now. Will make this multi-mailbox in the future
    search_folders = SEARCH_FOLDER
    search_folders = args.folder

    all_recipients = []
    for folder in search_folders:
        one_folder_recipients = get_recipients_from_folder(
            mail_conn, folder, start_date=start_date, before_date=before_date
        )
        logger.info("%s total recipients in %s", len(one_folder_recipients), folder)
        all_recipients.extend(one_folder_recipients)
        mail_conn.close()

    mail_conn.logout()

    logger.info("%s total recipients across %s", len(all_recipients), search_folders)
    unique_recipients = set(all_recipients)
    logger.info(
        "%s unique recipients across %s", len(unique_recipients), search_folders
    )
    unique_domains = set(map(lambda x: x[x.index("@") + 1 :], unique_recipients))
    logger.info("%s unique domains across %s", len(unique_domains), search_folders)

    # Very unsophisticated way of showing the recipient list
    if args.all_addresses is True:
        print("\nList of all recipients:", len(all_recipients))
        print("-------------------------------")
        pp(sorted(all_recipients))
    if args.unique_domains is True:
        print("\nList of UNIQUE domains:", len(unique_domains))
        print("-------------------------------")
        pp(sorted(unique_domains))
    if args.unique_addresses is True:
        print("\nList of all UNIQUE recipients:", len(unique_recipients))
        print("-------------------------------")
        pp(sorted(unique_recipients))


if __name__ == "__main__":
    main()
