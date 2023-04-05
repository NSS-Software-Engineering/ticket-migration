#!/usr/bin/env python3

import json
import argparse
import time
import gh
import migrator


def main(args):
    repos = []

    source_repo = gh.get_repo(args.source_repo, include_issues=True)

    if args.target_repo is not None:
        repos = [args.target_repo]
    elif args.config_file is not None:
        with open(args.config_file) as file:
            repos = json.load(file)['targetRepos']

    migrator.migrate(args.source_repo, repos, args.throttle_seconds)

    print('Migration complete')


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


if __name__ == '__main__':
    main(get_args())

