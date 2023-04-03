import subprocess
import json


def get_open_issues(repo):
    command = ['gh', 'issue', 'list',
               '--repo', repo,
               '--state', 'open',
               '--json', 'title,body',
               '--limit', '100']

    return json.loads(subprocess.check_output(command))


def get_repo(repo_with_onwer, include_issues=False):
    owner_name, repo_name = repo_with_onwer.split('/')

    command = _graphql_command(_gql_for_repo(owner_name, repo_name, include_issues))
    response = json.loads(subprocess.check_output(command))

    repository = response['data']['repository']
    result = {
        'id': repository['id'],
        'name': repo_name,
        'name_with_owner': f'{owner_name}/{repo_name}',
        'owner_id': repository['owner']['id'],
        'owner_name': owner_name,
    }

    if include_issues:
        result['issues'] = _from_gql_issues(repository['issues']['nodes'])

    return result


def create_project(repo):
    repo_id = repo['id']
    owner_id = repo['owner_id']
    project_title = repo['name']

    command = _graphql_command(_gql_to_create_project(owner_id, repo_id, project_title))
    response = json.loads(subprocess.check_output(command))

    return {
        'id': response['data']['createProjectV2']['projectV2']['id'],
        'title': response['data']['createProjectV2']['projectV2']['title'],
        'repo_id': repo_id,
        'owner_id': owner_id
    }


def create_label(repo, label):
    repo_id = repo['id']
    name = label['name']
    description = label['description']
    color = label['color']

    command = _graphql_command(_gql_to_create_label(repo_id, name, description, color))
    response = json.loads(subprocess.check_output(command))

    return {
        'id': response['data']['createLabel']['label']['id'],
        'repo_id': repo_id,
        'name': name,
        'description': description,
        'color': color
    }


def create_issue(repo, issue):
    repo_id = repo['id']
    title = issue['title']
    body = issue['body']
    label_ids = [label['id'] for label in issue['labels']]

    command = _graphql_command(_gql_to_create_issue(repo_id, title, body, label_ids))
    response = json.loads(subprocess.check_output(command))

    return {
        'id': response['data']['createIssue']['issue']['id'],
        'repo_id': repo_id,
        'title': title,
        'body': body
    }


def add_issue_to_project(project, issue):
    project_id = project['id']
    issue_id = issue['id']

    command = _graphql_command(_gql_to_add_issue_to_project(project_id, issue_id))
    response = json.loads(subprocess.check_output(command))

    return {
        'project_item_id': response['data']['addProjectV2ItemById']['item']['id'],
        'project_id': project_id,
        'issue_id': issue_id
    }


def _graphql_command(graphql):
    # Note: the last eleemnt of the command list is concatenated to avoid introducing a space
    return ['gh', 'api', 'graphql', '-f', 'query=' + graphql]


def _gql_for_repo(owner_name, repo_name, include_issues):
    gql = f'''\
query get_repo_with_issues {{
    repository(owner: "{owner_name}", name: "{repo_name}") {{
        id
        owner {{
            id
        }}
'''

    if include_issues:
        gql = gql + f'''\
        issues(first: 100, states: [OPEN]) {{
            nodes{{
                id
                title
                body
                labels(first:100) {{
                    nodes {{
                        id
                        name
                        description
                        color
                    }}
                }}
            }}
        }}'''

    gql = gql + f'''\
    }}
}}'''

    return gql


def _gql_to_create_project(owner_id, repo_id, title):
    return f'''\
mutation create_project_v2 {{
    createProjectV2 (
        input: {{ ownerId: "{owner_id}", repositoryId: "{repo_id}", title: "{title}" }}
    ) {{
        projectV2 {{
            id
            title
        }}
    }}
}}'''


def _gql_to_create_issue(repo_id, title, body, label_ids):
    return f'''\
mutation create_issue_in_project {{
    createIssue (input: {{
        repositoryId: {json.dumps(repo_id)},
        title: {json.dumps(title)},
        body: {json.dumps(body)},
        labelIds: {json.dumps(label_ids)}
    }}) {{
        issue {{
            id
        }}
    }}
}}'''


def _gql_to_add_issue_to_project(project_id, issue_id):
    return f'''\
mutation add_project_v2_item_by_id {{
    addProjectV2ItemById (
        input: {{ projectId: "{project_id}", contentId: "{issue_id}" }}
    ) {{
        item {{
            id
        }}
    }}
}}'''


def _gql_to_create_label(repo_id, name, description, color):
    return f'''\
mutation create_label {{
    createLabel (input: {{
        repositoryId: {json.dumps(repo_id)},
        name: {json.dumps(name)},
        description: {json.dumps(description)},
        color: {json.dumps(color)}
    }}) {{
        createLabel {{
            label {{
                id
            }}
        }}
    }}
}}'''


def _from_gql_issues(gql_issues):
    return [_from_gql_issue(gi) for gi in gql_issues]


def _from_gql_issue(gql_issue):
    return {
        'id': gql_issue['id'],
        'title': gql_issue['title'],
        'body': gql_issue['body'],
        'labels': gql_issue['labels']['nodes']
    }
