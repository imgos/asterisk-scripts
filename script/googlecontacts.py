#!/usr/bin/python
#
# There is a helper script to get your access_token and refresh token.
# Use get_google_oauth_tokens.py:
#  1. Run script with your client_id and client_secret
#  2. Go to the url it gives you
#  3. Log in
#  4. Paste auth code into script
#  5. It will give you the token values
#  6. Put those tokens in the json file this script uses
#
# Read the credentials info from a file that is formatted like so:
#
# {
#   "user@domain.com": {
#     "client_id": "...",
#     "client_secret": "...",
#     "scope": "https://www.googleapis.com/auth/contacts.readonly",
#     "user_agent": "python2",
#     "access_token": "...",
#     "refresh_token": "..."
#   }
# }

import atom
import json
import re
import sys
import os
import gdata.contacts
import gdata.contacts.service
import gdata.contacts.client

def main():
  country_code = "1"

  # delete all of our contacts before we refetch them, this will allow deletions
  os.system( "asterisk -rx \'database deltree cidname\'" )

  credentials = {
                  "user@domain.com":"from_json_file",
                }

  with open( '/var/lib/asterisk/extra/client_secrets.json' ) as f:
    clients = json.load( f )

  for cred_user, cred_pass in credentials.items():
    if cred_pass == 'from_json_file':
      # OAuth2
      gd_client = gdata.contacts.client.ContactsClient()
      oauth2_creds = gdata.gauth.OAuth2Token( client_id = clients[cred_user]['client_id'],
                                              client_secret = clients[cred_user]['client_secret'],
                                              scope = clients[cred_user]['scope'],
                                              user_agent = clients[cred_user]['user_agent'],
                                              access_token = clients[cred_user]['access_token'],
                                              refresh_token = clients[cred_user]['refresh_token'] )
      oauth2_creds.authorize( gd_client )

      query = gdata.contacts.client.ContactsQuery()
      query.max_results = 1000

      feed = gd_client.GetContacts( q=query )
    else:
      # old username/passwd way (no longer works with google apps)
      gd_client = gdata.contacts.service.ContactsService()
      gd_client.email = cred_user
      gd_client.password = cred_pass
      gd_client.source = 'gcontact2ast'
      gd_client.ssl = True
      gd_client.ProgrammaticLogin()

      query = gdata.contacts.service.ContactsQuery()
      query.max_results = 1000

      feed = gd_client.GetContactsFeed( query.ToUri() )

    # for each phone number in the contacts
    for i, entry in enumerate( feed.entry ):
      for phone in entry.phone_number:
        # Strip out any non numeric characters
        phone.text = re.sub('\D', '', phone.text)

        # Remove leading digit if it exists, we will add this again later for all numbers
        # Only if a country code is defined.
        if country_code != "":
          phone.text = re.sub( '^\+?%s' % country_code, '', phone.text )

        # Insert the number into the cidname database, reinsert the country code if defined.
        os.system( "asterisk -rx \'database put cidname +%s%s \"%s\"\'" % ( country_code, phone.text, entry.title.text ) )

if __name__ == "__main__":
        main()
