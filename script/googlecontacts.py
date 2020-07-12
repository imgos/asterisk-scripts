#!/usr/bin/python3
"""Get Google Contacts

Usage: google_contacts.py [--noauth_local_webserver]

Options:
    --noauth_local_webserver                  passed on to google auth
"""
import docopt
import httplib2
import subprocess
import unidecode

from apiclient import discovery
from argparse import Namespace
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

###


APPLICATION_NAME = "Asterisk DB Updater"

# If modifying these scopes, delete your previously saved credentials
SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/people.readonly",
]

OAUTH_CONFIG_FILE = "/etc/asterisk-scripts/asterisk_client_secrets.json"
OAUTH_TOKEN_FILE = "/etc/asterisk-scripts/asterisk_script_tokens.json"


###


def get_credentials(flags):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :param flags: oauth flags
    :return: the obtained credentials
    """
    store = Storage(OAUTH_TOKEN_FILE)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(OAUTH_CONFIG_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print(f"Storing credentials to: {OAUTH_TOKEN_FILE}")
    return credentials


def main():
    """Update asterisk db from google contacts"""
    opts = docopt.docopt(__doc__)
    flags = Namespace(
        auth_host_name="localhost",
        auth_host_port=[8080, 8090],
        logging_level="ERROR",
        noauth_local_webserver=opts["--noauth_local_webserver"],
    )

    credentials = get_credentials(flags)
    http = credentials.authorize(httplib2.Http())

    if opts["--noauth_local_webserver"]:
        return

    service = discovery.build("people", "v1", http=http)
    contacts_response = (
        service.people()
        .connections()
        .list(
            resourceName="people/me",
            personFields="names,phoneNumbers",
            sortOrder="LAST_NAME_ASCENDING",
        )
        .execute()
    )

    for i, contact in enumerate(contacts_response["connections"]):
        display_name = (
            contact["names"][0]["displayName"]
            if len(contact["names"]) > 0
            else "Unknown"
        )

        for phone in contact["phoneNumbers"]:
            ast_cmd = f'database put cidname {phone["canonicalForm"]} "{display_name}"'
            subprocess.run(["asterisk", "-rx", unidecode.unidecode(ast_cmd)])


if __name__ == "__main__":
    main()
