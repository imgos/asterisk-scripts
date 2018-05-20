#!/usr/bin/python
#
# See README.md for configuration information

import gdata.contacts.client
import gdata.contacts.service
import glob
import math
import os
import re
import sys
import unidecode
import xml.dom.minidom

import asteriskhelp

OAUTH_CONFIG_FILE = "/etc/asterisk-scripts/client_secrets.json"
USER_CONFIG_FILE = "/etc/asterisk-scripts/user_config.json"


def main():
    # load the configurations
    oauth_config = asteriskhelp.read_config(OAUTH_CONFIG_FILE)
    user_config = asteriskhelp.read_config(USER_CONFIG_FILE)

    for user_name, user_dict in user_config['users'].items():
        # OAuth2
        gd_client = gdata.contacts.client.ContactsClient()
        oauth2_creds = gdata.gauth.OAuth2Token(client_id=oauth_config['client_id'],
                                               client_secret=oauth_config['client_secret'],
                                               scope=oauth_config['scope'],
                                               user_agent=oauth_config['user_agent'],
                                               access_token=user_dict['access_token'],
                                               refresh_token=user_dict['refresh_token'])
        oauth2_creds.authorize(gd_client)

        query = gdata.contacts.client.ContactsQuery()
        query.max_results = 1000

        feed = gd_client.GetContacts(q=query)

        phonebook = []

        # for each phone number in the contacts
        for i, entry in enumerate(feed.entry):
            for phone in entry.phone_number:
                # Strip out any non numeric characters
                phone.text = re.sub('\D', '', phone.text)

                if user_config['country_code'] != "":
                    phone.text = re.sub('^\+?%s' % user_config['country_code'], '', phone.text)

                phone.text = re.sub('^', user_config['dialout_prefix'], phone.text)

                utf8_string = unidecode.unidecode(entry.title.text + ":::" + phone.text)
                phonebook.append(utf8_string)

        phonebook.sort()

        # just for convenience
        cisco = user_config['cisco_directory']

        pages = int(math.ceil((len(phonebook) + 0.0) / (int(cisco['max_entries_per_page']) + 0.0)))

        # remove the old phonebook if we'll be creating new pages
        # only really an issue if the new phonebook is smaller by at least one page
        if pages > 0:
            os.chdir(cisco['output_directory'])
            files = glob.glob("%s*%s" % (cisco['filename_base'], cisco['filename_extension']))
            for f in files:
                os.remove(f)

        for i in range(pages):
            create_ciscoipphonedirectory_file(
                phonebook[i * int(cisco['max_entries_per_page']): (i + 1) * int(cisco['max_entries_per_page'])],
                cisco['filename_base'],
                cisco['filename_extension'],
                cisco['output_directory'],
                cisco['base_url'],
                i,
                pages)


def print_dictionary(book):
    for item in book:
        sys.stdout.write(item + "\n")


def create_ciscoipphonedirectory_file(entries, filename_base, filename_extension,
                                      base_directory, base_url, page_number, total_pages):
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
        add_softkey(directory, main_element, "Prev",
                    base_url + filename_base + str(page_number - 1) + filename_extension, 4)

    if page_number < total_pages - 1:
        add_softkey(directory, main_element, "Next",
                    base_url + filename_base + str(page_number + 1) + filename_extension, 5)

    # end the xml document and save it
    uglyXML = directory.toprettyxml(indent='  ')
    text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
    prettyXML = text_re.sub('>\g<1></', uglyXML)

    filename = base_directory + filename_base + str(page_number) + filename_extension
    output_xml = open(filename, "w")
    output_xml.write(prettyXML)
    output_xml.close

    os.chmod(filename, 0644)


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
