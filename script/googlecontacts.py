#!/usr/bin/python
#
# See README.md for configuration information

import atom
import re
import sys
import os
import gdata.contacts.client

import asteriskhelp

OAUTH_CONFIG_FILE = "/etc/asterisk-scripts/client_secrets.json"
USER_CONFIG_FILE = "/etc/asterisk-scripts/user_config.json"


def main():
  # load the configurations
  oauth_config = asteriskhelp.read_config( OAUTH_CONFIG_FILE )
  user_config = asteriskhelp.read_config( USER_CONFIG_FILE )

  # remove old cid data from asterisk db
  os.system( "asterisk -rx \'database deltree cidname\'" )

  for user_username, user_dict in user_config['users'].items():
    # OAuth2
    g_client = gdata.contacts.client.ContactsClient()
    oauth2_creds = gdata.gauth.OAuth2Token( client_id=oauth_config['client_id'],
                                            client_secret=oauth_config['client_secret'],
                                            scope=oauth_config['scope'],
                                            user_agent=oauth_config['user_agent'],
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

        if user_config['country_code'] != "":
          phone.text = re.sub( '^\+?%s' % user_config['country_code'], '', phone.text )

        os.system( "asterisk -rx \'database put cidname +%s%s \"%s\"\'" % ( user_config['country_code'], phone.text, entry.title.text ) )


if __name__ == "__main__":
  main()
