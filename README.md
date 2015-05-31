# asterisk-scripts
A collection of convenience scripts for use with the asterisk PBX.

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
  }
}
```
