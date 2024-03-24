#!/usr/bin/env python3
"""Get Google Contacts

Usage: google_contacts.py [--noauth_local_webserver]

Options:
    --noauth_local_webserver                  passed on to google auth
"""
import apiclient
import argparse
import docopt
import httplib2
import oauth2client.client
import oauth2client.file
import oauth2client.tools
import subprocess
import unidecode

###


APPLICATION_NAME = "Asterisk Contacts Downloader"

# If modifying these scopes, delete your previously saved credentials
SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly",
]

OAUTH_CONFIG_FILE = "/etc/asterisk-scripts/client_secret.json"
OAUTH_TOKEN_FILE = "/etc/asterisk-scripts/asterisk_script_tokens.json"


###


def get_credentials(flags):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :param flags: oauth flags
    :return: the obtained credentials
    """
    store = oauth2client.file.Storage(OAUTH_TOKEN_FILE)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(OAUTH_CONFIG_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = oauth2client.tools.run_flow(flow, store, flags)
        print(f"Storing credentials to: {OAUTH_TOKEN_FILE}")
    return credentials


def main():
    """Update asterisk db from Google contacts"""
    opts = docopt.docopt(__doc__)
    flags = argparse.Namespace(
        auth_host_name="localhost",
        auth_host_port=[8080, 8090],
        logging_level="ERROR",
        noauth_local_webserver=opts["--noauth_local_webserver"],
    )

    credentials = get_credentials(flags)
    http = credentials.authorize(httplib2.Http())

    if opts["--noauth_local_webserver"]:
        return

    service = apiclient.discovery.build("people", "v1", http=http)
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

        phone_number_list = contact.get("phoneNumbers")
        if not phone_number_list:
            continue

        for phone in phone_number_list:
            if not phone.get("canonicalForm"):
                # consider using "value" instead
                continue

            ast_cmd = f'database put cidname {phone["canonicalForm"]} "{display_name}"'
            subprocess.run(["asterisk", "-rx", unidecode.unidecode(ast_cmd)])


if __name__ == "__main__":
    main()
