#!/usr/bin/python
#
# There is a helper script to get your access_token and refresh token.
#
# You must first register at the google developer console and get a
# client id and secret.
#
# Do that at: https://console.developers.google.com
#
# Create a new project
#
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
#   "country_code": "1",
#   "dialout_prefix": "9",
#   "users":
#     "user@domain.com": {
#       "client_id": "...",
#       "client_secret": "...",
#       "scope": "https://www.googleapis.com/auth/contacts.readonly",
#       "user_agent": "python2",
#       "access_token": "...",
#       "refresh_token": "..."
#     },
#     "anotheruser@domain.com": {
#       ...
#     }
#   }
# }

import atom
import json
import re
import sys
import os
import gdata.contacts.client

CONFIG_FILE = "/etc/asterisk-scripts/client_secrets.json"

def main():
  # load the configuration
  try:
    with open( CONFIG_FILE ) as f:
      configuration = json.load( f )
  except ValueError as e:
    print "Parse Error (file: \'%s\'): %s" % ( CONFIG_FILE, e )
    sys.exit()
  except IOError as e:
    print "Error reading configuration: %s" % ( e )
    sys.exit()

  # delete all of our contacts before we refetch them, this will allow deletions
  os.system( "asterisk -rx \'database deltree cidname\'" )

  for user_username, user_dict in configuration['users'].items():
    # OAuth2
    g_client = gdata.contacts.client.ContactsClient()
    oauth2_creds = gdata.gauth.OAuth2Token( client_id=user_dict['client_id'],
                                            client_secret=user_dict['client_secret'],
                                            scope=user_dict['scope'],
                                            user_agent=user_dict['user_agent'],
                                            access_token=user_dict['access_token'],
                                            refresh_token=user_dict['refresh_token'] )
    oauth2_creds.authorize( g_client )

    # limit the number of results returned (increase from the default of 25)
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000

    feed = g_client.GetContacts( q=query )

    for i, entry in enumerate( feed.entry ):
      for phone in entry.phone_number:
        phone.text = re.sub('\D', '', phone.text)

        if configuration['country_code'] != "":
          phone.text = re.sub( '^\+?%s' % configuration['country_code'], '', phone.text )

        os.system( "asterisk -rx \'database put cidname +%s%s \"%s\"\'" % ( configuration['country_code'], phone.text, entry.title.text ) )


if __name__ == "__main__":
  main()
