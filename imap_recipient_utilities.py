import imaplib
import sys
import ssl

import email.parser
import email.utils
from email.utils import parsedate_to_datetime
import logging

from email_message_constants import EmailMessageConstants

# DD-Mon-YYYY 31-Jan-2021
date_format_filter = "%d-%b-%Y"


class ImapRecipientUtilities:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # This should be injected
        self.emc = EmailMessageConstants()

    def connect(self, username, password, server):
        """Connect to [the specified] mail server. Return an open connection"""
        conn = imaplib.IMAP4_SSL(host=server, ssl_context=ssl.create_default_context())
        self.logger.info("Connection welcom: %s", conn.welcome)
        try:
            resp, data = conn.login(username, password)
            self.logger.info("Login returned: %s", resp)
        except imaplib.IMAP4.error:
            self.logger.error("Failed to login ")
            sys.exit(1)
        self.conn = conn

    def log_folders(self, conn):
        """logs a list of open mailbox folders"""
        for f in conn.list():
            for i in f:
                self.logger.info("    %s", i)

    def get_mails_from_folder(self, folder_name, start_date, before_date):
        """Fetch a specific folder (or label) from server"""
        # wrap in double quotes in case there are / or spaces
        typ, data = self.conn.select(mailbox='"%s"' % folder_name, readonly=True)
        if typ != "OK":
            self.logger.info("Could not open specific folder")
            self.log_folders(self.conn)
            return

        search_string = "ALL"
        search_string = '(since "%s" before "%s")' % (
            start_date.strftime(date_format_filter),
            before_date.strftime(date_format_filter),
        )

        typ, data = self.conn.search(None, search_string)
        if typ != "OK":
            self.logger.warn("Could not get mail list of folder: %s", folder_name)
            return

        return data[0].split()

    def fetch_message(self, msg_uid):
        """
        Fetch a specific message uid (not sequential id!) from the given folder;
        return the parsed message. User must ensure that specified
        message ID exists in that folder.
        """
        # TODO: Could we fetch just the envelope of the response to save bandwidth?
        typ, data = self.conn.fetch(msg_uid, "(RFC822)")
        if typ != "OK":
            self.logger.error("ERROR fetching message #%s", msg_uid)
            return

        return email.parser.BytesParser().parsebytes(data[0][1], headersonly=True)

    def get_summary_from_message(self, msg, folder_name, pattern_filter):
        """Given a parsed message, extract a dictionary with interesting fields"""
        message_definition = {}

        # store message identifiers
        message_definition[self.emc.label_message_date] = parsedate_to_datetime(
            msg[self.emc.label_message_date]
        ).strftime("%Y-%m-%d %H:%M:%S")
        message_definition[self.emc.label_folder] = folder_name
        message_definition[self.emc.label_message_id] = msg[self.emc.label_message_id]
        message_definition[self.emc.label_message_subject] = msg[
            self.emc.label_message_subject
        ]
        message_definition[self.emc.label_recipients] = []
        message_definition[self.emc.label_filtered] = []

        for f in self.emc.addr_fields:
            # wish we had TRACE
            # self.logger.debug("Examining Message %s", msg)
            # set it to empty in case the recipient type wasn't in the message
            message_definition[f] = []
            if msg[f] is not None:
                self.logger.debug("%s exists as %s", f, msg[f])
                address_tuples = email.utils.getaddresses(msg.get_all(f, []))
                # convert all to lower case for easier matching
                rlist = [x[1].lower() for x in address_tuples]
                self.logger.debug("getaddress: %s", rlist)
                message_definition[f] = rlist
                if rlist is not None:
                    self.logger.debug(
                        "appending %s to %s",
                        rlist,
                        message_definition[self.emc.label_recipients],
                    )
                    message_definition[self.emc.label_recipients].extend(rlist)
        # filter the assembled recipients list -- could change his to create filtered of each attribute
        filtered_address = pattern_filter(message_definition[self.emc.label_recipients])
        message_definition[self.emc.label_filtered].extend(filtered_address)

        if not message_definition[self.emc.label_recipients]:
            self.logger.error("Error no people attached to def %s", message_definition)
            self.logger.error("Error no people attached to msg %s", msg)
            exit()
        return message_definition

    def close_connection(self):
        self.conn.close()

    def logout(self):
        self.conn.logout()
