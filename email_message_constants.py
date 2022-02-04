class EmailMessageConstants:
    # dictionary and dataframe labels
    label_message_id = "Message-ID"
    label_message_date = "Date"
    label_folder = "Folder"
    label_message_subject = "Subject"
    label_recipients = "Recipients"
    label_filtered = "Filtered"
    label_from = "From"
    label_to = "To"
    label_cc = "Cc"
    label_bcc = "Bcc"
    label_reply_to = "Reply-To"
    label_sender = "Sender"
    # fields that contain mail addresses
    addr_fields = [
        label_from,
        label_to,
        label_cc,
        label_bcc,
        label_reply_to,
        label_sender,
    ]
    output_fields = [
        label_message_date,
        label_folder,
        label_message_id,
        label_message_subject,
        label_recipients,
        label_filtered,
        label_from,
        label_to,
        label_cc,
        label_bcc,
        label_reply_to,
        label_sender,
    ]
