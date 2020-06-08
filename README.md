# redmine-to-jira-confluence
Importer tool used to migrate issues and wiki pages from Redmine to Jira and Confluence. 

## Prerequisites
 * Python 3.4 or above installed on your machine 
 * Basic familiarity with running a Python script
 * All the dependencies must be installed on your machine (described in the Step-by-step guide)


## Step-by-step guide

 * You will find the requirements.txt file with the list of dependencies, please install them using the following command
   
   pip install -r requirements.txt
   
 * Once you have all the dependencies installed, you can start migrating Redmine issues or Wiki pages to Jira or Confluence.
 * More information can be provided using a YAML file. You will find two YAML files in the helpers directory.
 * Following three modes of migration are supported,
    
   1. Single page migration can be performed with the following command, 
    
      importer.py -w <Redmine Wiki page name (visible in the url)>
   
   2. Section migration is possible by executing the following command,

      importer.py -w <Redmine Section/Parent page name (visible in the url)> -m
    
      Different sections are visible on the Redmine Wiki index page.  All the child pages including their hierarchy will be migrated to Confluence. 

   3. Migration of all the Wiki pages under the given project can be achieved by the following command,

      importer.py -w 'Wiki' -a
   
      Entire pages including their relations and hierarchy will be migrated to Confluence. 
