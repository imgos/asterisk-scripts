# asterisk-scripts
A collection of convenience scripts for use with the asterisk PBX.

The configuration file should be placed at "/etc/asterisk-scripts/client_secrets.json".

```json
{
  "country_code": "1",
  "dialout_prefix": "9",
  "users": {
    "user@domain.com": {
      "client_id": "",
      "client_secret": "",
      "scope": "https://www.googleapis.com/auth/contacts.readonly",
      "user_agent": "python2",
      "access_token": "",
      "refresh_token": ""
    }
  }
}
```
