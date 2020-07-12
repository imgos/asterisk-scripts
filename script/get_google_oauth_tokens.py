#!/usr/bin/python3

import gdata.gauth

import asteriskhelp

CONFIG_FILE = "/etc/asterisk-scripts/client_secrets.json"


def main():
    config = asteriskhelp.read_config(CONFIG_FILE)

    token = gdata.gauth.OAuth2Token(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        scope=config["scope"],
        user_agent=config["user_agent"],
    )

    print(token.generate_authorize_url(redirect_uri="urn:ietf:wg:oauth:2.0:oob"))

    code = input("Enter verification code: ").strip()

    token.get_access_token(code)

    print(f"\nRefresh token: {token.refresh_token}")
    print(f"Access Token: {token.access_token}")


if __name__ == "__main__":
    main()
