#!/usr/bin/env python3
#
# See README.md for configuration information

import apiclient
import glob
import httplib2
import math
import oauth2client.client
import oauth2client.file
import oauth2client.tools
import os
import re
import unidecode
import xml.dom.minidom

import asteriskhelp

OAUTH_CONFIG_FILE = "/etc/asterisk-scripts/client_secrets.json"
OAUTH_TOKEN_FILE = "/etc/asterisk-scripts/asterisk_script_tokens.json"
USER_CONFIG_FILE = "/etc/asterisk-scripts/user_config.json"


def get_credentials():
    """Gets valid user credentials from storage.

    :return: the obtained credentials
    """
    store = oauth2client.file.Storage(OAUTH_TOKEN_FILE)
    return store.get()


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())

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

    user_config = asteriskhelp.read_config(USER_CONFIG_FILE)

    phonebook = contacts_to_pages(user_config, contacts_response)
    build_cisco_phonebook(user_config, phonebook)


def contacts_to_pages(user_config, contacts_response):
    phonebook = []

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

            phone_string = re.sub(r"\D", "", phone["canonicalForm"])

            if len(phone_string) != 11 or not phone_string.startswith("1"):
                # only support US phone numbers for now
                continue

            if user_config["country_code"] != "":
                phone_string = re.sub(
                    rf"^\+?{user_config['country_code']}", "", phone_string
                )

            phone_string = re.sub(r"^", user_config["dialout_prefix"], phone_string)

            utf8_string = unidecode.unidecode(f"{display_name}:::{phone_string}")
            phonebook.append(utf8_string)

    return phonebook


def build_cisco_phonebook(user_config, phonebook):
    # just for convenience
    cisco = user_config["cisco_directory"]

    pages = int(
        math.ceil((len(phonebook) + 0.0) / (int(cisco["max_entries_per_page"]) + 0.0))
    )

    # remove the old phonebook if we'll be creating new pages
    # only really an issue if the new phonebook is smaller by at least one page
    if pages > 0:
        os.chdir(cisco["output_directory"])
        files = glob.glob(f"{cisco['filename_base']}*{cisco['filename_extension']}")
        for f in files:
            os.remove(f)

    for i in range(pages):
        idx_start = i * int(cisco["max_entries_per_page"])
        idx_stop = (i + 1) * int(cisco["max_entries_per_page"])
        create_ciscoipphonedirectory_file(
            phonebook[idx_start:idx_stop],
            cisco["filename_base"],
            cisco["filename_extension"],
            cisco["output_directory"],
            cisco["base_url"],
            i,
            pages,
        )


def print_dictionary(book):
    for item in book:
        print(item + "\n")


def create_ciscoipphonedirectory_file(
    entries,
    filename_base,
    filename_extension,
    base_directory,
    base_url,
    page_number,
    total_pages,
):
    directory = xml.dom.minidom.Document()
    main_element = directory.createElement("CiscoIPPhoneDirectory")
    directory.appendChild(main_element)

    for entry in entries:
        name, number = entry.split(":::")

        # add this person to the directory
        entry_element = directory.createElement("DirectoryEntry")

        name_element = directory.createElement("Name")
        name_node = directory.createTextNode(name)
        name_element.appendChild(name_node)
        entry_element.appendChild(name_element)

        num_element = directory.createElement("Telephone")
        num_node = directory.createTextNode(number)
        num_element.appendChild(num_node)
        entry_element.appendChild(num_element)

        main_element.appendChild(entry_element)

    # add dial button
    add_softkey(directory, main_element, "Dial", "SoftKey:Dial", 1)

    # add editdial button
    add_softkey(directory, main_element, "EditDial", "SoftKey:EditDial", 2)

    # add exit button
    add_softkey(directory, main_element, "Exit", "SoftKey:Exit", 3)

    # add prev/next buttons
    if page_number > 0:
        add_softkey(
            directory,
            main_element,
            "Prev",
            base_url + filename_base + str(page_number - 1) + filename_extension,
            4,
        )

    if page_number < total_pages - 1:
        add_softkey(
            directory,
            main_element,
            "Next",
            base_url + filename_base + str(page_number + 1) + filename_extension,
            5,
        )

    # end the xml document and save it
    ugly_xml = directory.toprettyxml(indent="  ")
    text_re = re.compile(r">\n\s+([^<>\s].*?)\n\s+</", re.DOTALL)
    pretty_xml = text_re.sub(r">\g<1></", ugly_xml)

    filename = base_directory + filename_base + str(page_number) + filename_extension
    output_xml = open(filename, "w")
    output_xml.write(pretty_xml)
    output_xml.close()

    os.chmod(filename, 0o0644)


def add_softkey(xml_root, root_element, name, url, position):
    softkey_element = xml_root.createElement("SoftKeyItem")

    name_element = xml_root.createElement("Name")
    name_node = xml_root.createTextNode(name)
    name_element.appendChild(name_node)
    softkey_element.appendChild(name_element)

    url_element = xml_root.createElement("URL")
    url_node = xml_root.createTextNode(url)
    url_element.appendChild(url_node)
    softkey_element.appendChild(url_element)

    position_element = xml_root.createElement("Position")
    position_node = xml_root.createTextNode(str(position))
    position_element.appendChild(position_node)
    softkey_element.appendChild(position_element)

    root_element.appendChild(softkey_element)


if __name__ == "__main__":
    main()
