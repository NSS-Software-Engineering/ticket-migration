#!/usr/bin/env python3

import json
import argparse
import time
import copy
import gh


def main(args):
    repos = []

    source_repo = gh.get_repo(args.source_repo, include_issues=True)

    if args.target_repo is not None:
        repos = [args.target_repo]
    elif args.config_file is not None:
        with open(args.config_file) as file:
            repos = json.load(file)['targetRepos']

    for repo_name_with_owner in repos:
        migrate_tickets(source_repo, repo_name_with_owner, args.throttle_seconds)


def migrate_tickets(source_repo, target_repo_name_with_onwer, throttle_seconds):
    target_repo = gh.get_repo(target_repo_name_with_onwer)
    target_project = gh.create_project(target_repo)

    time.sleep(throttle_seconds)

    source_issues = source_repo['issues']
    source_labels = get_unique_labels(source_issues)

    source_to_target_labels = {}
    for source_label in source_labels:
        target_label = gh.create_label(target_repo, source_label)
        source_to_target_labels[source_label['id']] = target_label

        time.sleep(throttle_seconds)

    with_new_labels = transform_with_new_labels(source_issues, source_to_target_labels)

    for source_issue in with_new_labels:
        target_issue = gh.create_issue(target_repo, source_issue)
        gh.add_issue_to_project(target_project, target_issue)

        time.sleep(throttle_seconds)

    print(f'Tickets migrated for {target_repo_name_with_onwer}!')


def get_args():
    parser = argparse.ArgumentParser(
        'Migrate Issues from one GH repository to another')

    parser.add_argument('source_repo',
                        help="the <owner>/<name> name for the source repo",
                        type=str)

    parser.add_argument('--throttle_seconds',
                        help="number of second to wait between requests (default 5)",
                        default=5,
                        type=int)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--config_file',
                       help="path to a JSON config file",
                       default="config.json",
                       type=str)
    group.add_argument('--target_repo',
                       help="the <owner>/<name> name for the target repo",
                       type=str)

    return parser.parse_args()


def get_unique_labels(issues):
    label_dict = {
        label['id']: label
        for issue in issues
        for label in issue['labels']
    }
    return label_dict.values()


def transform_with_new_labels(issues, label_dict):
    tranformed = []

    for issue in issues:
        new_issue = copy.copy(issue)
        new_issue['labels'] = [
            label_dict[old_label['id']] for old_label in issue['labels']
        ]
        tranformed.add(new_issue)

    return tranformed


if __name__ == '__main__':
    main(get_args())

