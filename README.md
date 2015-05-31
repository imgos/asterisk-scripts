# asterisk-scripts
A collection of convenience scripts for use with the asterisk PBX.

The scripts in this repository use OAuth2.  So, yes, they will work with Google Apps accounts.

## googlecontacts.py

Import all of the telephone numbers from the contacts in Google accounts into the asterisk database.  Having the numbers available there, make is quick and easy to match inbound and outbound calls to a nicely-formatted name for display in caller ID, connected line information, CDR, etc.

## build_xml_directory.py

Import all of the phone numbers from the contacts of a Google account and format them into pages that can be served to Cisco phones as a directory.  This script will output all of the pages for the directory with the exception of the static base xml file (there is an example of that in this repo, etc/www/directory.xml).  Those files get served by an http server to the phones.  You'll just need to set the URL in the phone configuration to point to the location you are serving these files from.

## Configuration

Get your Client ID and Client Secret:

1. Register with the Google developer console (https://console.developers.google.com)
2. Create a new project
3. Under "APIs & Auth" -> "Credentials", use the button to create a new OAuth client ID
4. Choose "Installed Application"
5. Set a product name in the consent screen as requested
6. Set the "Installed Application Type" to "Other"
7. Click "Create Client ID"
8. Use the "Client ID" and "Client Secret" in the configuration file for these scripts (detailed below)

Use your Client ID and Client Secret to get OAuth Tokens.

1. Use the convenience script get_google_oauth_tokens.py
2. It gets its configuration from /etc/asterisk-scripts/client_secrets.json
3. Visit the URL the script gives you.
4. Authorize your application
5. Enter that code into the prompt the script gives
6. Use the resulting tokens in your user_config.json

### Configuration Files

The OAuth client configuration file should be placed at "/etc/asterisk-scripts/client_secrets.json".

```json
{
  "access_token": "",
  "refresh_token": "",
  "scope": "https://www.googleapis.com/auth/contacts.readonly",
  "user_agent": "python2"
}
```

The user configuration file should be placed at "/etc/asterisk-scripts/user_config.json".

```json
{
  "country_code": "1",
  "dialout_prefix": "9",
  "users": {
    "user@domain.com": {
      "access_token": "",
      "refresh_token": ""
    }
  },
  "cisco_directory": {
    "output_directory": "/var/www-unsec/asterisk/",
    "base_url": "http://10.0.100.3/asterisk/",
    "filename_base": "list",
    "filename_extension": ".xml",
    "max_entries_per_page": "32"
  }
}
```
