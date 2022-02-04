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
import getpass

from pprint import pprint as pp

import datetime
from datetime import date
import dateutil.relativedelta

from summaries_sink_csv import SummariesSinkCsv
from email_message_constants import EmailMessageConstants
from imap_recipient_utilities import ImapRecipientUtilities

import logging
from loggingconfig import load_logging

load_logging()
logger = logging.getLogger(__name__)

# argparse and IMAP search formats
# YYYY-MM-DD - 2021-01-30
date_format_input = "%Y-%m-%d"

# User may want to change these parameters if running script as-is
IMAP_SERVER_DEFAULT = "imap.gmail.com"
# Search folders, multiple directories can be given
# TODO: A user will want to change this
SEARCH_FOLDER = ["[Gmail]/Trash", "[Gmail]/All Mail", "INBOX"]

emc = EmailMessageConstants()
recip_utils = ImapRecipientUtilities()


def recipient_filter(recipient):
    """This function not yet implemented"""
    filtered = recipient
    logger.debug("filtering %s to %s", recipient, filtered)
    return filtered


def get_recipients_from_folder(folder_name, output_fields, start_date, before_date):
    """Read each message in a mailbox, write to CSV with folder name"""
    logger.info("Looking at folder %s", folder_name)

    folder_recipients = []
    mails = recip_utils.get_mails_from_folder(folder_name, start_date, before_date)
    # convert special characters to underscores - to support GMAIL standard names
    file_name = folder_name.translate(
        {ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-= +"}
    )
    sink = SummariesSinkCsv(file_name=file_name, output_fields=output_fields)
    sink_writer = sink.open_sink()

    if mails is not None:
        for mail_id in mails:
            data = recip_utils.fetch_message(mail_id)
            message_summary = recip_utils.get_summary_from_message(
                msg=data, folder_name=folder_name, pattern_filter=recipient_filter
            )
            logger.debug("%s", message_summary)
            sink_writer.write_row(message_summary)
            folder_recipients.extend(message_summary[emc.label_recipients])
        logger.info("Processed %s from %s", len(mails), folder_name)
    sink.close_sink()

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
        help="folder to scan. can Repeat. double quote if contains spaces.",
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
    recip_utils.connect(username=username, password=password, server=mail_server)

    if args.folder is None:
        # show folders of mail account
        recip_utils.log_folders()
        logger.error(
            "Must specify one of the folders above using --folder : Ex: --folder INBOX"
        )
        exit()

    # leave legacy code for now. Will make this multi-mailbox in the future
    search_folders = SEARCH_FOLDER
    # supports multiple folders on the command line
    search_folders = args.folder

    # TODO extract this into its own function
    all_recipients = []
    for folder in search_folders:
        one_folder_recipients = get_recipients_from_folder(
            folder,
            output_fields=emc.output_fields,
            start_date=start_date,
            before_date=before_date,
        )
        logger.info("%s total recipients in %s", len(one_folder_recipients), folder)
        all_recipients.extend(one_folder_recipients)
        recip_utils.close_connection()

    recip_utils.logout()

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
