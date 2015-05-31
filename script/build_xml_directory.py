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

import gdata.contacts.client
import gdata.contacts.service
import glob
import json
import math
import os
import re
import sys
import xml.dom.minidom

def main():
  country_code = "1"
  dialout_prefix = "9"

  output_directory = "/var/www-unsec/asterisk/"
  base_url = "http://10.0.100.3/asterisk/"
  filename_base = "list"
  filename_extension = ".xml"
  max_entries_per_page = 32

  credentials = {
                  "user@domain.com":"from_json_file",
                }

  with open( '/var/lib/asterisk/extra/client_secrets.json' ) as f:
    clients = json.load( f )

  for cred_user, cred_pass in credentials.items():

    if cred_pass == 'from_json_file':
      # OAuth2
      g_client = gdata.contacts.client.ContactsClient()
      oauth2_creds = gdata.gauth.OAuth2Token( client_id = clients[cred_user]['client_id'],
                                              client_secret = clients[cred_user]['client_secret'],
                                              scope = clients[cred_user]['scope'],
                                              user_agent = clients[cred_user]['user_agent'],
                                              access_token = clients[cred_user]['access_token'],
                                              refresh_token = clients[cred_user]['refresh_token'] )
      oauth2_creds.authorize( g_client )

      query = gdata.contacts.client.ContactsQuery()
      query.max_results = 1000

      feed = g_client.GetContacts( q=query )
    else:
      # old username/passwd way (no longer works with google apps)
      g_client = gdata.contacts.service.ContactsService()
      g_client.email = cred_user
      g_client.password = cred_pass
      g_client.source = 'gcontact2ast'
      g_client.ssl = True
      g_client.ProgrammaticLogin()

      query = gdata.contacts.service.ContactsQuery()
      query.max_results = 1000

      feed = g_client.GetContactsFeed( query.ToUri() )

    phonebook = []

    # for each phone number in the contacts
    for i, entry in enumerate( feed.entry ):
      for phone in entry.phone_number:
        # Strip out any non numeric characters
        phone.text = re.sub( '\D', '', phone.text )

        if country_code != "":
          phone.text = re.sub( '^\+?%s' % country_code, '', phone.text )

        phone.text = re.sub( '^', dialout_prefix, phone.text )

        phonebook.append( entry.title.text + ":::" + phone.text )

    phonebook.sort()

    pages = int( math.ceil( ( len( phonebook ) + 0.0 ) / ( max_entries_per_page + 0.0 ) ) )

    # remove the old phonebook if we'll be creating new pages
    # only really an issue if the new phonebook is smaller by at least one page
    if pages > 0:
      os.chdir( output_directory )
      files = glob.glob( "list*.xml" )
      for f in files:
        os.remove( f )

    for i in range( pages ):
      create_ciscoipphonedirectory_file(
        phonebook[ i * max_entries_per_page : ( i + 1 ) * max_entries_per_page ],
        filename_base,
        filename_extension,
        output_directory,
        base_url,
        i,
        pages )


def print_dictionary( book ):
  for item in book:
    sys.stdout.write( item  + "\n" )


def create_ciscoipphonedirectory_file( entries, filename_base, filename_extension,
                                       base_directory, base_url, page_number, total_pages ):
  directory = xml.dom.minidom.Document()
  main_element = directory.createElement( "CiscoIPPhoneDirectory" )
  directory.appendChild( main_element )

  for entry in entries:
    name, number = entry.split( ":::" )

    # add this person to the directory
    entry_element = directory.createElement( "DirectoryEntry" )

    name_element = directory.createElement( "Name" )
    name_node = directory.createTextNode( name )
    name_element.appendChild( name_node )
    entry_element.appendChild( name_element )

    num_element = directory.createElement( "Telephone" )
    num_node = directory.createTextNode( number )
    num_element.appendChild( num_node )
    entry_element.appendChild( num_element )

    main_element.appendChild( entry_element )

  # add dial button
  add_softkey( directory, main_element, "Dial", "SoftKey:Dial", 1 )

  # add editdial button
  add_softkey( directory, main_element, "EditDial", "SoftKey:EditDial", 2 )

  # add exit button
  add_softkey( directory, main_element, "Exit", "SoftKey:Exit", 3 )

  # add prev/next buttons
  if page_number > 0 :
    add_softkey( directory, main_element, "Prev",
      base_url + filename_base + str( page_number - 1 ) + filename_extension, 4 )

  if page_number < total_pages - 1:
    add_softkey( directory, main_element, "Next",
      base_url + filename_base + str( page_number + 1 ) + filename_extension, 5 )

  # end the xml document and save it
  uglyXML = directory.toprettyxml( indent='  ' )
  text_re = re.compile( '>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL )
  prettyXML = text_re.sub( '>\g<1></', uglyXML )

  filename = base_directory + filename_base + str( page_number ) + filename_extension
  output_xml = open( filename, "w" )
  output_xml.write( prettyXML )
  output_xml.close

  os.chmod( filename, 0644 )


def add_softkey( xml_root, root_element, name, url, position ):
  softkey_element = xml_root.createElement( "SoftKeyItem" )

  name_element = xml_root.createElement( "Name" )
  name_node = xml_root.createTextNode( name )
  name_element.appendChild( name_node )
  softkey_element.appendChild( name_element )

  url_element = xml_root.createElement( "URL" )
  url_node = xml_root.createTextNode( url )
  url_element.appendChild( url_node )
  softkey_element.appendChild( url_element )

  position_element = xml_root.createElement( "Position" )
  position_node = xml_root.createTextNode( str( position ) )
  position_element.appendChild( position_node )
  softkey_element.appendChild( position_element )

  root_element.appendChild( softkey_element )


if __name__ == "__main__":
  main()
