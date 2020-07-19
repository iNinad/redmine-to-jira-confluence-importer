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
    if redmine_issue.status.id in [5, 9]:
        print("Import is not allowed as the PBI: {0} is either in Finished or Cancelled state.".
              format(redmine_issue))
        return False
    return True


def is_migration_successful(confluence_page):
    """
    Checks whether the Confluence page is successfully created.
    Parameters:
        confluence_page (dict): Confluence page.
    Returns:
        True, if the Confluence page is successfully created. Otherwise False will be returned.
    """
    if 'statusCode' in confluence_page and int(str(confluence_page['statusCode'])[:1]) != 2:
        return False
    return True


def import_confluence_wiki(wiki_page_title):
    """
    Imports Redmine Wiki page in Confluence.
    Parameters:
        wiki_page_title (str): Title of the Redmine Wiki page to migrate.
    Returns:
        Function calls itself until all the pages are imported and returns 0, if successful.
    """
    wiki_page = settings.redmine.wiki_page.get(wiki_page_title,
                                               project_id=settings.yaml_vars['redmine_project_id'])
    if not settings.is_imported(wiki_page.text) and wiki_page.title not in settings.wiki_pages_imported:
        confluence_page = create_confluence_wiki(wiki_page)
        # Update the original Wiki page and add a link to the Confluence Page, if requested.
        if settings.arg_vars.remove:
            update_redmine_wiki(confluence_page, wiki_page)

    # Import child pages, if they are present.
    if wiki_page_title in settings.wiki_pages_rel:
        child_pages = settings.wiki_pages_rel[wiki_page_title].split(', ')
        for child_page in child_pages:
            if child_page:
                import_confluence_wiki(child_page)
    else:
        return 0


def create_confluence_wiki(wiki_page):
    """
    Creates a Confluence page from the given Redmine Wiki page.
    Parameters:
        wiki_page (obj): Redmine Wiki page to migrate.
    Returns:
        Confluence page (obj), if successful. Otherwise, it returns -1.
    """
    # Create a page in Confluence.
    new_title = wiki_page.title.replace('_', ' ')
    settings.current_page = wiki_page.title
    print("Creating a Confluence page: {}".format(new_title))
    try:
        wiki_content = settings.update_formatting(wiki_page.text.split('{{fnlist}}', 1)[0])
        wiki_page_first_version = settings.redmine.wiki_page.get(wiki_page.title,
                                                                 project_id=settings.yaml_vars['redmine_project_id'],
                                                                 version=1)
        # Add author and the last update details
        wiki_content += "\n----\n??Migrated from Redmine Wiki [{}|{}/projects/{}/wiki/{}]. " \
                        "Originally created on {} by {}. Last update on Redmine was on {} by {}??".format(
            wiki_page.title, settings.yaml_vars['redmine_server'],
            settings.yaml_vars['redmine_wiki_project'], wiki_page.title,
            wiki_page.created_on, wiki_page_first_version.author.name, wiki_page.updated_on, wiki_page.author.name)

        # Get the parent, if present
        confluence_parent_id = None
        # Check if parent attribute is present in the wiki_page
        if hasattr(wiki_page, 'parent'):
            wiki_parent = wiki_page.parent.title
            # check if the parent page is migrated to Confluence
            parent_wiki_page = settings.redmine.wiki_page.get(
                wiki_parent, project_id=settings.yaml_vars['redmine_project_id'])
            # check if page title is present in Confluence
            is_present = settings.confluence.page_exists(settings.yaml_vars['confluence_space'],
                                                         parent_wiki_page.title.replace('_', ' '))
            if is_present or parent_wiki_page.title in settings.wiki_pages_imported:
                confluence_parent_id = settings.confluence.get_page_id(settings.yaml_vars['confluence_space'],
                                                                       parent_wiki_page.title.replace('_', ' '))
            elif settings.is_imported(parent_wiki_page.text):
                parent_confluence_page = settings.get_confluence_page(parent_wiki_page.text)
                confluence_parent_id = parent_confluence_page['id']
                print("{}: Parent page found in Confluence: {}".format(
                    new_title, parent_confluence_page['title']))
        confluence_page = settings.confluence.create_page(
            space=settings.yaml_vars['confluence_space'],
            parent_id=confluence_parent_id,
            title=new_title,
            body=wiki_content,
            representation='wiki')

        while 'statusCode' in confluence_page and "UnknownMacroMigrationException: The macro " in \
                confluence_page['message']:
            unknown_macro = re.findall("The macro '(.*?)' is unknown", confluence_page['message'], 
                                       re.DOTALL)
            print("Previous attempt to create a Confluence page failed because of the unknown"
                  " macro : " + unknown_macro[0])

            if unknown_macro:
                search_unknown_macro = re.findall('{' + unknown_macro[0], wiki_content, re.IGNORECASE)
                for searched_macro in set(search_unknown_macro):
                    wiki_content = wiki_content.replace(searched_macro, '\\' + searched_macro)
                    wiki_content = wiki_content.replace('\\\\' + searched_macro, '\\' + searched_macro)

                if not search_unknown_macro and '{'+unknown_macro[0]+'}' in wiki_content:
                    print("Replacing : {"+unknown_macro[0]+"} with \\{"+unknown_macro[0]+"}")
                    wiki_content = wiki_content.replace('{'+unknown_macro[0]+'}',
                                                        '\\{'+unknown_macro[0]+'}')
                elif not search_unknown_macro and '{'+unknown_macro[0]+'}' not in wiki_content:
                    unknown_macro_index = re.search('{' + unknown_macro[0], wiki_content, re.IGNORECASE)
                    if unknown_macro_index:
                        match_found = unknown_macro_index.group()
                        print("Replacing : " + match_found + " with \\" + match_found )
                        wiki_content = wiki_content.replace(match_found, '\\' + match_found)
                        insensitive_hippo = re.compile(re.escape('{' + unknown_macro[0]), re.IGNORECASE)
                        if insensitive_hippo:
                            wiki_content = insensitive_hippo.sub('\\{' + unknown_macro[0], wiki_content)
                    else:
                        check_value = unknown_macro[0].strip().split('\n')[0]
                        unknown_macro_index = wiki_content.find(check_value)
                        if unknown_macro_index != -1:
                            while wiki_content[unknown_macro_index] != '{' and unknown_macro_index > 0:
                                unknown_macro_index = unknown_macro_index - 1
                            if wiki_content[unknown_macro_index] == '{':
                                print("{ is used with new line before :" + unknown_macro[0])
                                print("Replacing : { at the " + str(unknown_macro_index) + " index with \\{")
                                wiki_content = wiki_content[:unknown_macro_index] + \
                                               "\\{" + wiki_content[unknown_macro_index + 1:]

            print("Trying to create {} page again as the previous attempt was failed".format(wiki_page.title))
            confluence_page = settings.confluence.create_page(
                space=settings.yaml_vars['confluence_space'],
                parent_id=confluence_parent_id,
                title=new_title,
                body=wiki_content,
                representation='wiki')

        if not is_migration_successful(confluence_page):
            raise settings.ConfluenceImportError(confluence_page['statusCode'],
                                                 confluence_page['message'],
                                                 confluence_page['reason'])
        print("Created a new confluence page: {}".format(wiki_page.title))
        settings.wiki_pages_imported.add(wiki_page.title)

        # Add attachments
        add_attachments(wiki_page, confluence_page)

        # Add comments [NOT POSSIBLE TO FETCH THIS DATA FROM REDMINE VIA REST]
        # add_comments(wiki_page, confluence_page)

    except settings.ConfluenceImportError as error:
        print('Failed to create a confluence page {}: {}'.format(wiki_page.title, error))
        exit(-1)

    return confluence_page


def create_jira_issue(redmine_issue):
    """
    Create a new Jira issue from the given Redmine issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        Returns a newly created Jira issue (Resource object).
    """
    issue_type, redmine_work_type = get_issue_work_type(redmine_issue)
    issue_description, subject = update_subject_description(redmine_issue)

    issue_dict = {'project': settings.yaml_vars['jira_project'],
                  'summary': subject,
                  'description': issue_description,
                  'issuetype': {'name': settings.yaml_vars['issue_types'][issue_type]}
                  }

    # Add additional keys to the issue_dict depending on the issue_type
    if issue_type in ['ESCSTORY', 'ESCDOC', 'ESCCR']:
        is_esc_no = list(filter(lambda person: person['name'] == 'ESC Number',
                                redmine_issue.custom_fields))
        is_esc_ps_no = list(filter(lambda person: person['name'] == 'PS Number',
                                   redmine_issue.custom_fields))
        is_esc_found_version = list(filter(lambda person: person['name'] == 'Detected in Version',
                                           redmine_issue.custom_fields))
        esc_no = is_esc_no[0].value if is_esc_no else None
        esc_ps_no = is_esc_ps_no[0].value if is_esc_ps_no else None
        esc_found_version = is_esc_found_version[0].value if is_esc_found_version else None
        is_esc_priority = re.findall(r'\d+', redmine_issue.priority.name)
        if is_esc_priority:
            esc_priority = int(re.findall(r'\d+', redmine_issue.priority.name)[0])
        else:
            esc_priority = 'Default'
        issue_dict['customfield_14003'] = esc_ps_no
        issue_dict['customfield_14002'] = esc_no
        issue_dict['customfield_10104'] = esc_found_version
        issue_dict['priority'] = {'name': settings.yaml_vars['esc_priorites'][esc_priority]}

        if issue_type == 'ESCSTORY':
            esc_severity = list(filter(lambda person: person['name'] == 'Severity',
                                       redmine_issue.custom_fields))[0].value
            severity_no = int(re.findall(r'\d+', esc_severity)[0])
            issue_dict['customfield_14001'] = {
                'value': settings.yaml_vars['esc_stories'][severity_no]}

    elif issue_type == 'EPIC':
        # Add Epic name.
        issue_dict['customfield_10006'] = subject

    elif issue_type == 'SPIKE':
        # Update estimated hours, if available
        time_estimated = None
        if hasattr(redmine_issue, 'estimated_hours'):
            time_estimated = redmine_issue.estimated_hours
        else:
            match = re.findall("ED:\s([-+]?\d*\.*\d+)", issue_description)
            if match:
                time_estimated = match[0] + 'd'
        # Acceptance Criteria parsing is not supported.
        # Default string is added as it is a mandatory field for any spike story.
        issue_dict['customfield_10205'] = [{"name": "As per in the description"}]
        if time_estimated:
            # Remaining estimate is set to time_estimated, as it will be updated
            # when we modify the logged time on this issue.
            issue_dict['timetracking'] = {"originalEstimate": time_estimated,
                                          "remainingEstimate": time_estimated}

    # Check if Target version/Fix version field is available
    issue_fixed_version = None
    if hasattr(redmine_issue, 'fixed_version'):
        issue_fixed_version = settings.yaml_vars['fix_versions'].get(
            redmine_issue.fixed_version.name)
    if issue_fixed_version:
        issue_dict['fixVersions'] = [{'name': issue_fixed_version}]

    try:
        # Create a Jira issue
        new_issue = settings.jira.create_issue(fields=issue_dict)
        print("Created a new issue : {}".format(new_issue.key))
    except Exception as e:
        print("Failed to create a Jira issue: {}".format(e.text))
        exit(-1)

    # Update the reporter
    author_id = redmine_issue.author.id
    update_reporter(author_id, new_issue)

    # Update Work Type
    if issue_type != 'EPIC':
        work_type = settings.yaml_vars['work_type'][redmine_work_type]
        new_issue.update(fields={'customfield_11706': {'value': work_type}})
        print("{}: Updated R&D Work Type to {}".format(new_issue.key, work_type))

    # Update Time Spent
    if redmine_issue.spent_hours:
        time_spent = str(redmine_issue.spent_hours) + 'h'
        settings.jira.add_worklog(new_issue, timeSpent=time_spent)
        print("{}: Added the time spent to {}".format(new_issue.key, time_spent))

    # Update relations
    relate_issues(new_issue, redmine_issue)

    # Update Story Points
    if issue_type != 'EPIC':
        records = reversed(list(item for item in redmine_issue.journals if hasattr(item, 'details')))
        for record in records:
            for detail in record.details:
                # Update story points
                if detail.get('property', '') == 'attr' and \
                        detail.get('name', '') == 'story_points' and \
                        detail.get('new_value') is not None:
                    new_issue.update(customfield_10002=int(detail.get('new_value')))
                    print("{}: Updated Story Points to {}".format(new_issue.key,
                                                                  detail.get('new_value')))
                    break
            else:
                continue
            break

    # Update Live Demo and fetch the PO role, ready status and the reviewed status.
    is_ready = 'no'
    is_reviewed = 'no'
    po_role = None
    for field in redmine_issue.custom_fields:
        if field.name == 'Live Demo':
            live_demo = field.value.capitalize()
            new_issue.update(fields={'customfield_13504': {'value': live_demo}})
            print("{}: Updated Live Demo to {}".format(new_issue.key, live_demo))
        if field.name == 'Is Ready':
            is_ready = field.value.lower()
        if field.name == 'Is Reviewed':
            is_reviewed = field.value.lower()
        if field.name == 'PO Role':
            po_role = field.value.lower()

    # Update the Assignee
    if po_role:
        po_user = settings.redmine.user.filter(name=po_role)
        if po_user:
            po_username = get_login(po_user[0].id)
            update_assignee(new_issue, redmine_issue, po_username)
    else:
        update_assignee(new_issue, redmine_issue)

    # Update Issue status
    # If the issue is reviewed, ready and in New state change the status to 'Ready' in Jira.
    if redmine_issue.status.name.lower() == 'new' and is_ready == 'yes' and is_reviewed == 'yes':
        update_status(new_issue, 'to do', 'issue')
    else:
        update_status(new_issue, redmine_issue.status.name.lower(), 'issue')

    # Add attachments.
    add_attachments(redmine_issue, new_issue)

    # Add comments.
    add_comments(redmine_issue, new_issue)

    # Add sub-tasks (along with their attachments and comments).
    if issue_type != 'EPIC':
        add_subtasks(redmine_issue, new_issue)
    else:
        print("Sub-tasks (child backlog items) of the epic stories are not imported. But you can "
              "link the PBI to this epic while importing from Redmine.\n"
              "You just have to use -e {} in the command line.".format(new_issue.key))

    # Update Jira Epic link, if provided in the command line.
    if settings.arg_vars.epic:
        new_issue.update(fields={'customfield_10005': settings.arg_vars.epic})
        print("{}: Updated Epic link to {}".format(new_issue.key, settings.arg_vars.epic))

    return new_issue


def get_issue_work_type(redmine_issue):
    """
    Get the issue and work type for the given Redmine issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
    Returns:
        issue_type (str):  Issue type.
        redmine_work_type (str):  Work Type.
    """
    # Retrieve all the tags in the Redmine issue subject and determine the issue and work type.
    type_search = re.findall(r"\[([A-Za-z-0-9_]+)\]+", redmine_issue.subject)
    if 'SPIKE' in type_search:
        issue_type = 'SPIKE'
    elif redmine_issue.tracker.name == 'Epic':
        issue_type = 'EPIC'
    elif redmine_issue.tracker.name == 'Support Case':
        redmine_work_type = 'M'
        esc_documentation = list(filter(lambda person: person['name'] == 'ESC Documentation',
                                        redmine_issue.custom_fields))[0].value.lower()
        if esc_documentation == 'no':
            issue_type = 'ESCSTORY'
        else:
            issue_type = 'ESCDOC'
        return issue_type, redmine_work_type
    elif redmine_issue.tracker.name == 'Enhancement Request':
        redmine_work_type = 'M'
        issue_type = 'ESCCR'
        return issue_type, redmine_work_type

    else:
        items = [item for item in type_search if item in list(settings.yaml_vars['issue_types'].keys())]
        issue_type = 'DEFAULT' if not items else items[0]
    work_types = [item for item in type_search
                  if item in list(settings.yaml_vars['work_type'].keys())]
    redmine_work_type = work_types[0] if work_types else 'NPD'
    return issue_type, redmine_work_type


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
    subject = redmine_issue.subject.rpartition(']')[-1].strip()
    if not subject:
        subject = redmine_issue.subject.partition('[')[0].strip()
        if not subject:
            subject = redmine_issue.subject
    tags = redmine_issue.subject.rpartition(']')[0].strip()
    issue_relations = get_relations(redmine_issue.id)
    relation_description = '' if not issue_relations else '\n\n*Redmine issue relations:*\n'
    for relation in issue_relations:
        relation_description += '\n* #{} {} #{}'.format(relation.get('issue_id'),
                                                        relation.get('relation_type'),
                                                        relation.get('issue_to_id'))

    issue_description = '{} {} {} \n\n*Migrated from Redmine #{}* \n'.format(
        redmine_issue.description, get_checklists(redmine_issue.id),
        relation_description, redmine_issue.id)
    issue_description = settings.update_formatting(issue_description)
    if tags:
        tags += ']'
        issue_description += '\n Tags from the Redmine issue: {}'.format(tags)
    return issue_description, subject


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
    settings.redmine.issue.update(redmine_issue.id,
                                  subject='{} [JIRA-{}]'.format(redmine_issue.subject, jira_issue_id),
                                  description='{} \n*Migrated to JIRA "{}":{}/browse/{}*'.format(
                                      redmine_issue.description, jira_issue_id,
                                      settings.yaml_vars['jira_server'],
                                      jira_issue_id))
    print("{}: Added reference to the Jira issue".format(redmine_issue.id))


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
    confluence_url = confluence_page['_links']['base'] + confluence_page['_links']['webui']
    reference_sentence = '\n*Migrated to Confluence "{}":{}*'.format(confluence_page['title'],
                                                                     confluence_url)
    wiki_page.text += reference_sentence
    wiki_page.save()
    print("{}: Added reference to the Confluence page".format(wiki_page.title))


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
    try:
        issue_relations = get_relations(redmine_issue.id)
        # Iterate through each relation.
        for relation in issue_relations:
            related_issue_id = relation.get('issue_to_id') \
                if relation.get('issue_id') == redmine_issue.id else relation.get('issue_id')
            related_issue = settings.redmine.issue.get(related_issue_id)
            # Check if the related issue is imported in Jira.
            if settings.is_imported(related_issue.subject) \
                    and relation.get('relation_type') in list(settings.yaml_vars['issue_relations'].keys()):
                related_jira_id = re.search(r"\[JIRA-([A-Za-z0-9-]+)\]", related_issue.subject).group(1)
                link_type = settings.yaml_vars['issue_relations'].get(relation.get('relation_type'))
                if relation.get('issue_id') == redmine_issue.id:
                    inward_issue, outward_issue = jira_issue.key, related_jira_id
                else:
                    inward_issue, outward_issue = related_jira_id, jira_issue.key
                # Create a link.
                settings.jira.create_issue_link(
                    type=link_type,
                    inwardIssue=inward_issue,
                    outwardIssue=outward_issue
                )
                print("{}: Created {} link to {}".format(jira_issue.key,
                                                         link_type, related_jira_id))
    except Exception as e:
        print('{}: Could not relate issues : {}'.format(jira_issue.key, e))


def update_reporter(author_id, jira_issue):
    """
    Updates the reporter of the Jira issue.
    Parameters:
        author_id (int): Redmine User ID of the author.
        jira_issue (obj): Jira issue (Resource object).
    Returns:
        None.
    """
    try:
        author_username = get_login(author_id)
        if author_username:
            jira_issue.update(reporter={'name': author_username})
            print("{}: Updated the reporter to {}".format(jira_issue.key, author_username))
    except Exception as e:
        print('{}: Could not update the reporter : {}'.format(jira_issue.key, e.text))


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
    try:
        # Check if the assigned_to field exists.
        if hasattr(redmine_issue, 'assigned_to'):
            # Check if the assignee is a team or a PO.
            if redmine_issue.assigned_to.name in list(settings.yaml_vars['teams'].keys()):
                assigned_team = settings.yaml_vars['teams'][redmine_issue.assigned_to.name]
                jira_issue.update(fields={'customfield_12802': [{'value': assigned_team}]})
                print("{}: Updated Team to {}".format(jira_issue.key, assigned_team))
            if redmine_issue.assigned_to.name in list(settings.yaml_vars['assignee'].keys()):
                # Assign it to the PO of the team.
                assigned_po = settings.yaml_vars['assignee'][redmine_issue.assigned_to.name]
                po_user = settings.redmine.user.filter(name=assigned_po)
                if po_user:
                    po_userlogin = get_login(po_user[0].id)
                    if po_userlogin:
                        jira_issue.update(assignee={'name': po_userlogin})
                        print("{}: Updated the assignee to {}".format(jira_issue.key, po_userlogin))
                    else:
                        print(
                            "Assignee login for {} does not exists.".format(redmine_issue.assigned_to.name))
            elif not po_username:
                # Assign it to the individual team member.
                author_username = get_login(redmine_issue.assigned_to.id)
                if author_username:
                    jira_issue.update(assignee={'name': author_username})
                    print("{}: Updated the assignee to {}".format(jira_issue.key, author_username))
                else:
                    print("Assignee login for {} does not exists.".format(redmine_issue.assigned_to.name))
        if po_username:
            jira_issue.update(assignee={'name': po_username})
            print("{}: Updated the assignee to {}".format(jira_issue.key, po_username))
    except Exception as e:
        print('{}: Could not update the assignee : {}'.format(jira_issue.key, e.text))


def add_attachments(source, destination):
    """
    Get all the attachments from a given Redmine issue and add them them to the Jira issue.
    Parameters:
        source (obj): Redmine issue (Resource object).
        destination (obj): Jira issue (Resource object).
    Returns:
        None.
    """
    try:
        for item in source.attachments:
            attachment = settings.redmine.attachment.get(item.id)
            file_path = attachment.download(savepath='.', filename=item.filename)
            if settings.arg_vars.pbi:
                settings.jira.add_attachment(issue=destination, attachment=file_path, filename=item.filename)
                print("{}: Added attachment: {}".format(destination.key, item.filename))
            elif settings.arg_vars.wiki:
                status = settings.confluence.attach_file(filename=file_path,
                                                         name=item.filename,
                                                         page_id=destination['id'],
                                                         title=destination['title'],
                                                         space=settings.yaml_vars['confluence_space'])
                if status is None:
                    print("{}: Failed to add attachment: {}".format(source.title, item.filename))
                elif not is_migration_successful(status):
                    raise settings.ConfluenceImportError(status['statusCode'], status['message'],
                                                         status['reason'])
                else:
                    print("{}: Added attachment: {}".format(source.title, item.filename))
            os.remove(file_path)
    except settings.ConfluenceImportError as error:
        print('Failed to add an attachmentConfluenceImportError to a confluence page: {}'.
              format(error))
    except Exception as e:
        if settings.arg_vars.pbi:
            print('{}: Could not add attachment: {}', destination.key, e)
        elif settings.arg_vars.wiki:
            print('{}: Could not add attachment: {}', destination, e)


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
    for record in source.journals:
        if hasattr(record, 'notes') and record.notes.strip():
            comment_author = record.user.name
            comment = settings.update_formatting(record.notes)
            if comment.strip():
                comment_description = "Commented by: {}\n{}".format(comment_author, comment)
                if settings.arg_vars.pbi:
                    settings.jira.add_comment(destination, comment_description)
                    print("{}: Added Comment: {}...".format(destination.key, record.notes[:15]))
                elif settings.arg_vars.wiki:
                    settings.confluence.add_comment(destination['id'], comment_description)
                    print("{}: Added Comment: {}...".format(destination['id'], record.notes[:15]))


def add_subtasks(redmine_issue, jira_issue):
    """
    Get all the sub-tasks from a given Redmine issue and add them them to the Jira issue.
    Parameters:
        redmine_issue (obj): Redmine issue (Resource object).
        jira_issue (obj): Jira issue (Resource object).
    Returns:
        None.
    """
    for child in redmine_issue.children:
        subtask = settings.redmine.issue.get(child.id)
        subtask_dict = {
            'project': {'key': settings.yaml_vars['jira_project']},
            'summary': subtask.subject,
            'issuetype': {'name': 'Sub-task'},
            'parent': {'id': jira_issue.key},
        }

        # Check if the assigned_to field exists.
        if hasattr(subtask, 'assigned_to'):
            # Check if the assignee is a team as it is now mandatory for creating a task.
            if subtask.assigned_to.name in list(settings.yaml_vars['teams'].keys()):
                assigned_team = settings.yaml_vars['teams'][subtask.assigned_to.name]
                subtask_dict['customfield_12802'] = [{'value': assigned_team}]

        child = settings.jira.create_issue(fields=subtask_dict)
        print("{}: Created sub-task {} ".format(jira_issue.key, child.key))
        update_assignee(child, subtask)
        update_status(child, subtask.status.name.lower(), 'subtask')
        add_comments(subtask, child)
        add_attachments(subtask, child)


