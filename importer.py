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


main()

