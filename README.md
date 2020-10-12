# redmine-to-jira-confluence
Importer tool can be used to **migrate issues and wiki pages from Redmine to Jira and Confluence**.

## Prerequisites
 * Python 3.4 or above installed on your machine
 * Basic familiarity with running a Python script
 * All the dependencies must be installed on your machine (described in the Step-by-step guide)

## Step-by-step guide

 * You will find the requirements.txt file with the list of dependencies, please install them using the following command

   `pip install -r requirements.txt`
  
 * Once you have all the dependencies installed, you can start migrating Redmine issues or Wiki pages to Jira or Confluence.
 * More information can be provided using a YAML file. You will find two YAML files in the helpers directory.
 * **For Redmine Wiki to Confluence migration**, following **three modes** are supported,
    
   -  **Single page** migration can be performed with the following command,
   
      `importer.py -w <Redmine Wiki page name (visible in the url)>`
   
   -  **Section** migration is possible by executing the following command,
  
      `importer.py -w <Redmine Section/Parent page name (visible in the url)> -m`
   
      Different sections are visible on the Redmine Wiki index page.  All the child pages including their hierarchy will be migrated to Confluence.

   -  Migration of **all Wiki pages** under the given project can be achieved by the following command,

      `importer.py -w 'Wiki' -a`
  
      Entire pages including their relations and hierarchy will be migrated to Confluence.

* You can start migrating issues from Redmine to JIRA with a simple command like,

     `importer.py -i <Redmine PBI number>`
    
## Further Notes

* Following arguments are supported by the tool,

    `importer.py [-h] (-i PBI | -w WIKI) [-m] [-a] [-r] [-e EPIC] [-rk REDMINEKEY] [-rp REDMINEPROJECT] [-ju JIRAUSER] [-jk JIRAKEY] [-jp JIRAPROJECT] 
    [-cs CONFLUENCESPACE] [-yml YAML]`
 
      optional arguments:
        -h, --help                                 Show this help message and exit
        -m, --multiple                             Import a section (parent with all the child pages) to Confluence
        -a, --all                                  Import all the pages from a given Redmine project to Confluence
        -r, --remove                               Remove the original Redmine Wiki content and add a link to the Confluence page
        -e, --epic <EPIC>                          Related Epic number in Jira, if any
        -rk, --redminekey <REDMINEKEY>             Redmine API key
        -rp, --redmineproject <REDMINEPROJECT>     Redmine Project name
        -ju, --jirauser <JIRAUSER>                 Jira User
        -jk, --jirakey <JIRAKEY>                   Jira API key
        -jp, --jiraproject <JIRAPROJECT>           Jira Project used for importing the issues
        -cs, --confluencespace <CONFLUENCESPACE>   Confluence Space used for importing the Wiki pages
        -yml, --yaml <YAML filename>               YAML file to use, it should be present in the helpers directory

      required arguments:
        -w WIKI, --wiki WIKI                       Title of the Redmine wiki page to migrate to Confluence`

* Some of the information (like Redmine project, Confluence space name etc.) is stored in the YAML file. This information will be overridden by the values provided via arguments.
* If you wish to replace the contents of the original Redmine Wiki page with a link to the newly created Confluence page, use -r argument.
* Please make sure that the Importer user has all the required permissions on the Confluence space.

## Known issues
* Color markup is not supported by Confluence, the tool will transform all the colored text from Redmine to the bold format in Confluence while migration.
* Confluence does not support table cell alignment, table row/column span etc via markup.
* Some of the Redmine markups are not compatible with Confluence, like the Markups for collapse, popular pages and includes.
