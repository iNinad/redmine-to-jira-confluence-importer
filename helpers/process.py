import helpers.settings as settings
import os
import re


def get_login(user_id):
    """
    Retrieves the username of a given user.
    Parameters:
        user_id (int): User ID in Redmine.
    Returns:
        Returns the username, if found. Otherwise None will be returned.
    """
    url = "{}/users/{}.json".format(settings.yaml_vars['redmine_server'], user_id)
    json_data = settings.request_redmine(url)
    if json_data:
        user = json_data.get('user')
        if user.get('login'):
            return user.get('login')
    else:
        return None


def get_relations(issue_id):
    """
    Retrieves the relations of a Redmine issue.
    Parameters:
        issue_id (int): Issue ID in Redmine.
    Returns:
        Returns a dictionary with all the relations.
    """
    url = "{}/issues/{}/relations.json".format(settings.yaml_vars['redmine_server'], issue_id)
    json_data = settings.request_redmine(url)
    return json_data["relations"]


def get_pages_info():
    """
    Retrieves the Redmine Wiki pages title - parent information.
    Returns:
        Returns a dictionary with all the relations.
    """
    url = "{}/projects/{}/wiki/index.json".format(settings.yaml_vars['redmine_server'],
                                                  settings.yaml_vars['redmine_project_id'])
    json_data = settings.request_redmine(url)
    return json_data["wiki_pages"]


def get_checklists(issue_id):
    """
    Retrieves the checklist defined in a Redmine issue.
    Parameters:
        issue_id (int): Issue ID in Redmine.
    Returns:
        Returns a formatted string with the checklist.
    """
    url = "{}/issues/{}/checklists.json".format(settings.yaml_vars['redmine_server'], issue_id)
    json_data = settings.request_redmine(url)
    checklists = [(checklist.get('subject'), checklist.get('is_done'))
                  for checklist in json_data['checklists']]
    result = ''
    if checklists:
        result = '\n\n*Checklist:*\n'
        for checklist in checklists:
            if checklist[1] is not None:
                result += '* (/) -{}-\n'.format(checklist[0])
            else:
                result += '* {}\n'.format(checklist[0])
    return result


def validate_issue(redmine_issue):
    """
    Check if a given Redmine issue is either in Finished or Cancelled state.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        Returns True if a given Redmine issue is not in Finished or Cancelled state, otherwise False.
    """


def is_migration_successful(confluence_page):
    """
    Checks whether the Confluence page is successfully created.
    Parameters:
        confluence_page (dict): Confluence page.
    Returns:
        True, if the Confluence page is successfully created. Otherwise False will be returned.
    """


def import_confluence_wiki(wiki_page_title):
    """
    Imports Redmine Wiki page in Confluence.
    Parameters:
        wiki_page_title (str): Title of the Redmine Wiki page to migrate.
    Returns:
        Function calls itself until all the pages are imported and returns 0, if successful.
    """


def create_confluence_wiki(wiki_page):
    """
    Creates a Confluence page from the given Redmine Wiki page.
    Parameters:
        wiki_page (obj): Redmine Wiki page to migrate.
    Returns:
        Confluence page (obj), if successful. Otherwise, it returns -1.
    """


def create_jira_issue(redmine_issue):
    """
    Create a new Jira issue from the given Redmine issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        Returns a newly created Jira issue (Resource object).
    """


def get_issue_work_type(redmine_issue):
    """
    Get the issue and R&D work type for the given Redmine issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        issue_type (str):  Issue type.
        redmine_work_type (str):  R&D Work Type.
    """


def update_subject_description(redmine_issue):
    """
    Removes all the tags in the issue subject, add them at the bottom.
    Add Redmine issue relations and a link to the Redmine issue in the description.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        issue_description (str):  Issue description.
        subject (str):  Issue subject.
    """


def update_status(jira_issue, redmine_issue_status, category):
    """
    Updates the status of a Jira issue.
    Parameters:
        jira_issue (obj): Jira issue (Resource object).
        redmine_issue_status (str): Redmine issue status.
        category (str): Category of the issue.
    Returns:
        None.
    """


def update_redmine_issue(jira_issue_id, redmine_issue):
    """
    Updates the Redmine issue by adding a tag in the subject and a link to the newly created JIRA
    issue in the description.
    Parameters:
        jira_issue_id (int): Jira issue ID.
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        None.
    """


def update_redmine_wiki(confluence_page, wiki_page):
    """
    Updates the Redmine wiki by adding a tag in the subject and a link to the newly created
    Confluence page in the description.
    Parameters:
        jira_issue_id (int): Jira issue ID.
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        None.
    """


def relate_issues(jira_issue, redmine_issue):
    """
    Read each related Redmine issue to see if it has already been migrated. If so, add the relation
    link, otherwise it ignore the relation as it will be set when the related PBI is migrated.
    Parameters:
        jira_issue (obj): Jira issue (Resource object).
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        None.
    """


def update_reporter(author_id, jira_issue):
    """
    Updates the reporter of the Jira issue.
    Parameters:
        author_id (int): Redmine User ID of the author.
        jira_issue (obj): Jira issue (Resource object).
    Returns:
        None.
    """


def update_assignee(jira_issue, redmine_issue, po_username=None):
    """
    Updates the assignee of the Jira issue.
    Parameters:
        jira_issue (obj): Jira issue (Resource object).
        redmine_issue (obj): Redmine issue (Resource object).
        po_username (str): PO username.
    Returns:
        None.
    """


def add_attachments(source, destination):
    """
    Get all the attachments from a given Redmine issue and add them them to the Jira issue.
    Parameters:
        source (obj): Redmine issue (Resource object).
        destination (obj): Jira issue (Resource object).
    Returns:
        None.
    """


def add_comments(source, destination):
    """
    Get all the comments from a given Redmine issue and add them them to the Jira issue.
    As the author of the comment cannot be modified, the author name is added in the comment
    description.
    Parameters:
        source (obj): Redmine issue (Resource object).
        destination (obj): Jira issue (Resource object).
    Returns:
        None.
    """


def add_subtasks(redmine_issue, jira_issue):
    """
    Get all the sub-tasks from a given Redmine issue and add them them to the Jira issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
        jira_issue (obj): Jira issue (Resource object).
    Returns:
        None.
    """


