import argparse
import json
import requests
import yaml


class ConfluenceImportError(Exception):

    # Constructor or Initializer
    def __init__(self, value, message, reason):
        self.value = value
        self.message = message
        self.reason = reason

    # __str__ is to print() the value
    def __str__(self):
        return "{}:{}-{}".format(self.value, self.message, self.reason)


def init():
    """
    Initialize global variables and connections to the Redmine and Jira servers.
    Parameters:
        None.
    Returns:
        None.
    """


def get_config_data(file_path):
    """
    Helper method to retrieve and use the YAML file to initialize a dictionary.
    Parameters:
        file_path (str): .yaml file path.
    Returns:
        A dictionary with key-values from the .yaml file.
    """
    try:
        with open(file_path) as file_handle:
            config = yaml.safe_load(file_handle)
            return config
    except Exception as e:
        print('Could not load {0}:\n {1}'.format(file_path, e))


def get_args():
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(description='Process arguments for exporting issue/Wiki to Jira/Confluence')
    required_named = parser.add_mutually_exclusive_group(required=True)
    required_named.add_argument('-i', '--pbi', action='store',
                                help='Remine PBI number to migrate to the Jira')
    required_named.add_argument('-w', '--wiki', action='store',
                                help='Title of the Redmine wiki page to migrate to Confluence')
    parser.add_argument('-m', '--multiple', action='store_true',
                        help='Import a section (parent with all the child pages) to Confluence')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Import all the pages from a given Redmine project to Confluence')
    parser.add_argument('-r', '--remove', action='store_true',
                        help='Remove the original Redmine Wiki content and add a link to the Confluence page')
    parser.add_argument('-e', '--epic', action='store', help='Related Epic no. in Jira, if any')
    parser.add_argument('-rk', '--redminekey', action='store', help='Redmine API key')
    parser.add_argument('-rp', '--redmineproject', action='store', help='Redmine Project name')
    parser.add_argument('-ju', '--jirauser', action='store', help='Jira User')
    parser.add_argument('-jk', '--jirakey', action='store', help='Jira API key')
    parser.add_argument('-jp', '--jiraproject', action='store',
                        help='Jira Project used for importing the issues')
    parser.add_argument('-cs', '--confluencespace', action='store',
                        help='Confluence Space used for importing the Wiki pages')
    parser.add_argument('-yml', '--yaml', action='store',
                        help='YAML file to use, it should be present in the helpers directory')
    args = parser.parse_args()
    return args


def get_headers():
    """
    Return headers used in the REST call to the Redmine server.
    Parameters:
        None.
    Returns:
        A dictionary with the header values.
    """


def request_redmine(url):
    """
    Send HTTP/REST requests to the Redmine server.
    Parameters:
        url (str): URL including the REST endpoint.
    Returns:
        A dictionary with the response values.
    """
    try:
        resp = requests.get(url, headers=get_headers())
        resp.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Connection error while contacting the Redmine server.")
        return None
    except requests.exceptions.HTTPError:
        print("Internal Server error")
        return None
    else:
        json_data = json.loads(resp.text)
        return json_data


def is_imported(subject):
    """
    Check if a given Redmine issue is already imported in Jira.
    Parameters:
        subject (str): Subject of a Redmine issue.
    Returns:
        Returns True if a given Redmine issue is already imported in Jira, otherwise False.
    """


def get_confluence_page(description):
    """
    Retrieves the Confluence page object from it's reference in the original Redmine Wiki page.
    Parameters:
        description (str): Redmine Wiki page description.
    Returns:
        Returns the Confluence page object, if found. Otherwise None will be returned.
    """


def update_formatting(description):
    """
    Updates formatting of the issue and comment description before importing in Jira.
    Parameters:
        description (str): Description from the Redmine issue/comment.
    Returns:
        Returns a formatted string.
    """

