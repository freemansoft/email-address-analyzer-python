## Purpose
Data acquisition tool to extract all entities communicated with via email.
Intended to be used looking for recipient hacking or unexpected email address.

* Queries specified IMAP folders and retrieves all participants for a given mailbox in a specified date range
* Writes results to a csv file with same name as the IMAP mailbox/folder
* Can scan multiple mailboxes in a given date range


## USAGE 
The default date range _one week_ of messages _prior to_ today.

```
usage: main.py [-h] -u USERNAME -p PASSWORD [-if FOLDER] [-sd START_DATE] [-bd BEFORE_DATE] [--imap-server IMAP_SERVER] [-oud] [-oad] [-oua] [-fa ADDRESS_FILTER] [-fd DOMAIN_FILTER]

Retrieve recipients from matching mailboxes and date range and write to csv files.

optional arguments:
  -h, --help                              show this help message and exit
  -u USERNAME, --username USERNAME
                                          the email username not optional
  -p PASSWORD, --password PASSWORD
                                          the email password not optional
  -if FOLDER, --imap-folder FOLDER
                                          folder to scan. can repeat. double quote if contains spaces.
  -sd START_DATE, --start-date START_DATE
                                          start date Default: 2022-01-26
  -bd BEFORE_DATE --before-date BEFORE_DATE
                                          prior to date Default: 2022-02-02
  --imap-server IMAP_SERVER
                                          imap server Default: imap.gmail.com
  -oud, --unique-domains
                                          output is unique domains
  -oad, --all-addresses
                                          output is all addresses
  -oua, --unique-addresses
                                          output is unique addresses
  -fa ADDRESS_FILTER, --filter-address ADDRESS_FILTER
                                          address to filter from results. Can repeat
  -fd DOMAIN_FILTER, --filter-domain DOMAIN_FILTER
                                          domain to filter from results. Can repeat                                                               
```

Get usage help with 

* `python3 extract-all-recipients.py -h` 

Sample execution for gmail scanning Sent Mail and INBOX

* `python3 main.py --username foo@bar.com --password <password or app token> --imap-folder INBOX`
* `python3 main.py --username foo@bar.com --password <password or app token> --imap-folder "[Gmail]/Sent Mail" --imap-folder INBOX -oua -sd 2021-12-31`
* `python3 main.py --username foo@bar.com --password <password or app token> --imap-folder "[Gmail]/Sent Mail" --imap-folder INBOX -oua -fd deathstar.gov`

### Password
The app currently requires that you enter your password on the command line which isn't great.

*Users with MFA* would instead use an application token as your password.  GMail has a screen where you can get a token for program use. 
Note that the token essentially bypasses MFA so destroy the token when you are done with your mail operations.

### Filtering
The program can filter out addresses or domains as specified on the command line.  Filters do not apply to individual recipient columns in the CSV.

Filtered values are removed :
* The _Filtered_ column in the CSV 
* From the command line console output `-oua`, `-oud`, `-oad`

## Output

Mailbox data is written to a csv file with the same name
* `INBOX` --> `INBOX.csv`
* `[Gmail]/ Sent Mail` --> `_Gmail_Sent_Mail.csv`

### Sample CSv
```
Date,Folder,Message-ID,Subject,Recipients,Filtered,From,To,Cc,Bcc,Reply-To,Sender
2022-01-25 23:07:08, INBOX, <9887-383B7C066439@domain1.com>,Is there a librarian?,"['alumni@domain2.com', 'alumni@domain2.com', 'kevin@domain1.com']","['alumni@domain2.com', 'alumni@domain2.com', 'kevin@domain1.com']",['alumni@domain2.com'],['alumni@domain2.com'],[],[],['kevin@domain1.com'],[]
```
### Command line log
Looking at two GMail mailboxes from 2022-02-03 **until** today.  Output formatted for clarity
```
$ python3 main.py --username foo@bar.com --password <some_secret> --imap-folder "[Gmail]/Sent Mail" --imap-folder INBOX -oua -sd 2022-02-03

2022-02-04 19:22:48,234; INFO    ; imap_recipient_utilities ; connect                       ;  25; Connection welcom: b'* OK Gimap ready for requests from 108.48.69.33 u11mb99851888qtw'
2022-02-04 19:22:48,571; INFO    ; imap_recipient_utilities ; connect                       ;  28; Login returned: OK

2022-02-04 19:22:48,571; INFO    ; __main__                 ; get_recipients_from_folder    ;  61; Looking at folder [Gmail]/Sent Mail
2022-02-04 19:22:48,958; INFO    ; __main__                 ; get_recipients_from_folder    ;  83; Processed 1 from [Gmail]/Sent Mail
2022-02-04 19:22:48,958; INFO    ; __main__                 ; main                          ; 241; 2 total recipients in [Gmail]/Sent Mail

2022-02-04 19:22:49,034; INFO    ; __main__                 ; get_recipients_from_folder    ;  61; Looking at folder INBOX
2022-02-04 19:22:50,157; INFO    ; __main__                 ; get_recipients_from_folder    ;  83; Processed 9 from INBOX
2022-02-04 19:22:50,157; INFO    ; __main__                 ; main                          ; 241; 25 total recipients in INBOX

2022-02-04 19:22:50,250; INFO    ; __main__                 ; main                          ; 248; 27 total recipients across ['[Gmail]/Sent Mail', 'INBOX']
2022-02-04 19:22:50,250; INFO    ; __main__                 ; main                          ; 250; 10 unique recipients across ['[Gmail]/Sent Mail', 'INBOX']
2022-02-04 19:22:50,250; INFO    ; __main__                 ; main                          ; 254; 7 unique domains across ['[Gmail]/Sent Mail', 'INBOX']
Filtered of all UNIQUE recipients: 10
-------------------------------
['customercare@deathstar.gov',
 'donotreply-comm@xxx.com',
 'dsmith@xxx.com',
 'bounce@xxx.com',
 'izaak@xxx.org',
 'joe@xxx.com',
 'membership@xxxx.org',
 'mymy@xxx.com',
 'no-reply@xxxx.com',
 'noreply@xxxx.com']
```
Notes
1. The _Recipients_ column contains all the addresses in the other fields.
1. The _Filtered_ column is identical to the _Recipients_ column as filtering is not yet implemented

Debug output and other levels of loggng are written to
* warning.log
* info.log
* debug.log

## Source Code
Source auto-formatted by visual studio code using the default settings

### Unit Tests
There is some unit test coverage but not much.

Run tests with
```
python3 -m unittest
```
