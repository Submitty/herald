#!/usr/bin/env python3
"""Generate a draft for the release notes."""

from argparse import ArgumentParser
import re
import sys

import requests

BASE_API_URL = "https://api.github.com/repos/Submitty/Submitty"
VERSION = '0.3.0'
TYPE_REGEX = re.compile(r"^\[([ a-zA-Z0-9]+):*([ a-zA-Z0-9]*)\](.*)")


def get_commit_details(message, commit_types):
    lines = message.splitlines()
    commit_message = lines[0].strip()
    commit_category = None
    commit_type = 'Bugfix'
    commit_subtype = ''
    message = commit_message
    try:
        re_match = re.match(TYPE_REGEX, commit_message)
        commit_type = re_match.group(1).replace(' ', '')
        commit_subtype = re_match.group(2).replace(' ', '')
        message = re_match.group(3).strip()
        if commit_type.lower() in ['ui']:
            commit_type = 'Feature'
            if commit_subtype == '':
                commit_subtype = 'UI'
        if commit_subtype.lower() in ['testing', 'test', 'tests', 'vagrant']:
            commit_subtype = 'Testing'
        if commit_type.lower() in ['devdependency','dependencydev']:
            if commit_type.lower() == 'dependencydev':
                commit_type = 'DevDependency'
            commit_category = 'dependency'
        elif commit_type.lower() not in commit_types:
            commit_type = 'Bugfix' if commit_subtype == '' else commit_subtype
        elif commit_subtype.lower() == 'testing':
            commit_subtype = commit_type
            commit_type = 'Testing'
    except AttributeError:
        commit_type = "Bugfix"

    final_message = f'[{commit_type}'
    if commit_subtype != '':
        final_message += f":{commit_subtype}"
    final_message += f"] {message}"
    return final_message, commit_category if commit_category is not None else commit_type.lower()


def main(args):
    """Generate the release notes."""
    req = requests.get(f"{BASE_API_URL}/releases/latest")
    previous_release = req.json()

    parser = ArgumentParser(description="Generates release notes for Submitty")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument(
        "--from",
        type=str,
        dest="from_tag",
        default=previous_release['tag_name'],
        help="Set release tag to compare from. Defaults to last release."
    )
    parser.add_argument(
        "--to",
        type=str,
        default="master",
        help="Set release to compare to. Defaults to HEAD of master."
    )

    args = parser.parse_args(args)

    req = requests.get(
        f"{BASE_API_URL}/compare/{args.from_tag}...{args.to}"
    )

    commits = req.json()['commits']

    release_commits = {
        "security": {
            "title": "SECURITY",
            "commits": []
        },
        "breaking": {
            "title": "BREAKING",
            "commits": []
        },
        "feature": {
            "title": "FEATURE / ENHANCEMENT",
            "commits": []
        },
        "vpat": {
            "title": "VPAT",
            "commits": []
        },
        "bugfix": {
            "title": "BUGFIX",
            "commits": []
        },
        "refactor": {
            "title": "REFACTOR",
            "commits": []
        },
        "dependency": {
            "title": "SUPPORTING REPOSITORIES & VENDOR PACKAGES",
            "commits": []
        },
        "testing": {
            "title": "TESTING / BUILD",
            "commits": []
        },
        "documentation": {
            "title": "DOCUMENTATION",
            "commits": []
        }
    }

    for commit_obj in commits:
        message, commit_type = get_commit_details(
            commit_obj['commit']['message'],
            release_commits.keys()
        )
        release_commits[commit_type]['commits'].append(f"{message}")

    release_notes = ""

    previous_link = f"[{previous_release['tag_name']}]({previous_release['html_url']})"
    release_notes += f"*Previous Release Notes:* {previous_link}\n"
    release_notes += "\n"
    for release_type in release_commits:
        release_notes += f"{release_commits[release_type]['title']}\n\n"
        if len(release_commits[release_type]['commits']) == 0:
            release_notes += "*None*\n"
        else:
            for commit in sorted(release_commits[release_type]['commits']):
                release_notes += f"* {commit}\n"
        release_notes += "\n"

    print(release_notes)


if __name__ == "__main__":
    main(sys.argv[1:])
