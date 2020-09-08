"""
Python program for exporting issues/wiki pages from Remine to Jira/Confluence
"""

import helpers.process as process
import helpers.settings as settings
import logging


logging.basicConfig(level=logging.CRITICAL, filename='importer.log')
logger = logging.getLogger('importer')


def main():
    """
    Simple command-line program for exporting an issue from Remine to Jira.
    """
    # Initialize global variables and connections to the Redmine and Jira/Confluence servers.

    settings.init()

    # Perform Remine to Jira/Confluence migration.
    if settings.arg_vars.pbi:
        try:
            # Fetch the Redmine issue.
            redmine_issue = settings.redmine.issue.get(settings.arg_vars.pbi)
            if process.validate_issue(redmine_issue):
                if not settings.is_imported(redmine_issue.subject):
                    # Create an issue in Jira.
                    jira_issue = process.create_jira_issue(redmine_issue)
                    # Update the Remine issue.
                    process.update_redmine_issue(jira_issue.key, redmine_issue)
                else:
                    print("PBI is already imported in Jira")
        except Exception as e:
            print("Failed while importing the Redmine issue {}: {}".format(
                settings.arg_vars.pbi, e))

    elif settings.arg_vars.wiki:
        try:
            settings.wiki_pages_rel = dict()
            settings.wiki_pages_imported = set()
            if settings.arg_vars.multiple or settings.arg_vars.all:
                # Fetch Redmine wiki pages and initialize a dict with Parent - Child relations.
                wiki_pages = process.get_pages_info()
                for page in wiki_pages:
                    if 'parent' in page:
                        if page['parent']['title'] not in settings.wiki_pages_rel:
                            settings.wiki_pages_rel[page['parent']['title']] = page['title']
                        else:
                            if not settings.wiki_pages_rel[page['parent']['title']]:
                                settings.wiki_pages_rel[page['parent']['title']] = page['title']
                            else:
                                settings.wiki_pages_rel[page['parent']['title']] += ', ' + page[
                                    'title']
                    else:
                        if page['title'] not in settings.wiki_pages_rel:
                            settings.wiki_pages_rel[page['title']] = ''

                if settings.arg_vars.all:
                    for wiki_page in settings.wiki_pages_rel:
                        if wiki_page not in settings.wiki_pages_imported:
                            process.import_confluence_wiki(wiki_page)

            if not settings.arg_vars.all:
                process.import_confluence_wiki(settings.arg_vars.wiki)

        except Exception as e:
            print("Failed while importing the Redmine Wiki - {} : {}".format(
                settings.arg_vars.wiki, e))

        finally:
            print("Migrated {} pages to Confluence".format(len(settings.wiki_pages_imported)))


main()

