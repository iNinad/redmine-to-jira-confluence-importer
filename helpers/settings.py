from atlassian import Confluence
from jira import JIRA
from redminelib import Redmine
import argparse
import base64
import json
import re
import requests
import os
import urllib3
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
    global yaml_vars, arg_vars, redmine, jira, confluence, wiki_pages_rel, wiki_pages_imported, current_page
    dir_path = os.path.dirname(os.path.realpath(__file__))
    arg_vars = get_args()

    # Check if the .yaml file provided in the command line arguments, if yes, use the provided file.
    # Otherwise, use 'vars.yaml'.
    yaml_vars = get_config_data(os.path.join(dir_path, arg_vars.yaml)) if arg_vars.yaml is not None \
        else get_config_data(os.path.join(dir_path, 'vars.yaml'))
    # Check if Redmine API key, Jira user and Jira project is provided in the command line.
    # If yes, overwrite variables which are initialized from the .yaml file.
    if arg_vars.redminekey:
        yaml_vars['redmine_apikey'] = arg_vars.redminekey
    if arg_vars.redmineproject:
        yaml_vars['redmine_wiki_project'] = arg_vars.redmineproject
    if arg_vars.jirauser:
        yaml_vars['jira_user'] = arg_vars.jirauser
    if arg_vars.jiraproject:
        yaml_vars['jira_project'] = arg_vars.jiraproject
    if arg_vars.confluencespace:
        yaml_vars['confluence_space'] = arg_vars.confluencespace
    # Initialize the redmine instance.
    redmine = Redmine(yaml_vars['redmine_server'], key=yaml_vars['redmine_apikey'],
                      requests={'timeout': 10})
    redmine_project = redmine.project.get(yaml_vars['redmine_wiki_project'])
    yaml_vars['redmine_project_id'] = redmine_project.id
    # Suppress the InsecureRequestWarnings.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Initialize the jira instance.
    jira = JIRA({'server': yaml_vars['jira_server'], 'verify': False},
                basic_auth=(yaml_vars['jira_user'],
                            base64.b64decode(yaml_vars['jira_password']).decode("utf-8")))
    confluence = Confluence(url=yaml_vars['confluence_server'],
                            username=yaml_vars['confluence_user'],
                            password=base64.b64decode(yaml_vars['confluence_password']).decode("utf-8"))


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
    return {'X-Redmine-API-Key': yaml_vars['redmine_apikey'], 'content-type': 'application/json'}


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
    if arg_vars.pbi and '[JIRA-{}-'.format(yaml_vars['jira_project']) in subject:
        return True
    elif arg_vars.wiki and '*Migrated to Confluence "' in subject:
        return True
    else:
        return False


def get_confluence_page(description):
    """
    Retrieves the Confluence page object from it's reference in the original Redmine Wiki page.
    Parameters:
        description (str): Redmine Wiki page description.
    Returns:
        Returns the Confluence page object, if found. Otherwise None will be returned.
    """
    if arg_vars.wiki and '*Migrated to Confluence "' in description:
        match_patterns = re.findall(r"\*Migrated to Confluence \"(.*?)\"", description)
        for match_pattern in match_patterns:
            confluence_page = confluence.get_page_by_title(yaml_vars['confluence_space'], match_pattern)
            if confluence_page is not None:
                return confluence_page
    else:
        return None


def update_formatting(description):
    """
    Updates formatting of the issue and comment description before importing in Jira.
    Parameters:
        description (str): Description from the Redmine issue/comment.
    Returns:
        Returns a formatted string.
    """
    formatted_description = description.replace('<pre><code class', '<code class')
    formatted_description = formatted_description.replace('</code></pre>', '</code>')
    formatted_description = formatted_description.replace('<pre>', '{noformat}')
    formatted_description = formatted_description.replace('</pre>', '{noformat}')
    match_inline_codes = re.findall(r"\@(.*?)\@", formatted_description)
    for matched_inline_code in set(match_inline_codes):
        formatted_description = formatted_description.replace(
            '@{}@'.format(matched_inline_code), '{{' + matched_inline_code + '}}')
    formatted_description = formatted_description.replace('*READY FOR MIGRATION TO JIRA*', '')
    match_pbis = re.findall('#(\d+)', formatted_description)
    for matched_pbi in set(match_pbis):
        formatted_description = formatted_description.replace(
            '#{}'.format(matched_pbi), '[#{}|{}/issues/{}]'.format(
                matched_pbi, yaml_vars['redmine_server'], matched_pbi))

    if arg_vars.wiki:
        formatted_description = formatted_description.replace('{{>toc}}', '{toc}')
        # Replace || with | | to render an empty cell of the table in Confluence
        formatted_description = formatted_description.replace('||', '| | ')
        formatted_description = formatted_description.replace('|_.', '||')
        formatted_description = formatted_description.replace('|^.', '|')
        formatted_description = formatted_description.replace('|>.', '|')
        formatted_description = formatted_description.replace('|<.', '|')
        formatted_description = formatted_description.replace('|~.', '|')
        formatted_description = formatted_description.replace('|=.', '|')
        formatted_description = formatted_description.replace('|_<.', '||')
        formatted_description = formatted_description.replace('<notextile>', '')
        formatted_description = formatted_description.replace('</notextile>', '')
        formatted_description = formatted_description.replace('<code>', '{code}')
        formatted_description = formatted_description.replace('</code>', '{code}')
        match_source_code = re.findall(r"<code class=\"(.*?)\">", formatted_description)
        match_child_macro = re.findall(r"{{child_pages\(depth=(.*?)\)}}", formatted_description)
        # Need to redesign the following replace as [] can occur in the code or within {nofomat}
        # or {code} macros
        match_single_square_markup = re.findall(r"\[(.*?)\]", formatted_description)
        match_double_square_markup = re.findall(r"\[\[(.*?)\]\]", formatted_description)
        match_pc_markup = re.findall(r"%(.*?)%", formatted_description)
        match_bg_markup = re.findall(r"{background:(.*?)}", formatted_description)
        try:

            for matched_code in set(match_pc_markup):
                formatted_description = formatted_description.replace(
                    '%{}%'.format(matched_code),
                    '*{}*'.format(matched_code))

            for matched_code in set(match_bg_markup):
                formatted_description = formatted_description.replace(
                    '{{background:{}}}'.format(matched_code), '')

            for matched_code in set(match_source_code):
                formatted_description = formatted_description.replace(
                    '<code class="{}">'.format(matched_code),
                    '{{code:language={}}}'.format(matched_code))
            for matched_macro in set(match_child_macro):
                formatted_description = formatted_description.replace(
                    '{{child_pages(depth={0})}}'.format(matched_macro),
                    'children:sort=creation|depth={0}'.format(matched_macro))
            for matched_square_markup in set(match_single_square_markup):
                if not matched_square_markup.startswith('[') and \
                        matched_square_markup[1:] not in set(match_double_square_markup):
                    formatted_description = formatted_description.replace(
                        '[{0}]'.format(matched_square_markup),
                        '[[{0}]]'.format(matched_square_markup))
            for matched_square_markup in set(match_double_square_markup):
                link = matched_square_markup.split('|')[0].split('#')[0]
                try:
                    correct_title = link.replace(' ', '_').replace('.', '')
                    if ':' in correct_title:
                        redmine_project = correct_title.split(':')[0]
                        correct_title = correct_title.split(':')[1]
                    else:
                        redmine_project = yaml_vars['redmine_project_id']
                    wiki_page = redmine.wiki_page.get(correct_title, project_id=redmine_project)
                except Exception as e:
                    wiki_page = None
                    print("Could not find a Redmine Wiki page with title - {}".format(link))
                if wiki_page:
                    if arg_vars.all:
                        if redmine_project == yaml_vars['redmine_project_id']:
                            formatted_description = formatted_description.replace(
                                '[[{0}]]'.format(matched_square_markup),
                                '[{0}]'.format(wiki_page.title.replace('_', ' ')))
                        else:
                            # If the page is on another Wiki project, add link to the the original Redmine Wiki page.
                            formatted_description = formatted_description.replace(
                                '[[{0}]]'.format(matched_square_markup),
                                "[{}|{}/projects/{}/wiki/{}]".format(link, yaml_vars['redmine_server'],
                                                                     redmine_project,
                                                                     wiki_page.title.replace('_', ' ')))
                    else:
                        is_present = confluence.page_exists(yaml_vars['confluence_space'],
                                                            wiki_page.title.replace('_', ' '))
                        if is_present:
                            formatted_description = formatted_description.replace(
                                '[[{0}]]'.format(matched_square_markup),
                                '[{0}]'.format(wiki_page.title.replace('_', ' ')))
                        elif wiki_page.title == current_page:
                            formatted_description = formatted_description.replace(
                                '[[{0}]]'.format(matched_square_markup),
                                '[{0}]'.format(matched_square_markup.split('|')[0].replace('_', ' ')))
                        else:
                            # If the page is not present in Confluence, add link to the the original Redmine Wiki page.
                            formatted_description = formatted_description.replace(
                                '[[{0}]]'.format(matched_square_markup),
                                "[{}|{}/projects/{}/wiki/{}]".format(link, yaml_vars['redmine_server'],
                                                                     redmine_project,
                                                                     wiki_page.title.replace('_', ' ')))
                formatted_description = formatted_description.replace(
                    '[[{0}]]'.format(matched_square_markup),
                    '[{0}]'.format(matched_square_markup))
        except Exception as e:
            print(e)

    return formatted_description

