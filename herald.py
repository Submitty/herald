#!/usr/bin/env python3
"""Generate a draft for the release notes."""

from argparse import ArgumentParser
import re

import requests

BASE_API_URL = "https://api.github.com/repos/Submitty/Submitty"


def main():
    """Generate the release notes."""
    req = requests.get(f"{BASE_API_URL}/releases/latest")
    previous_release = req.json()

    parser = ArgumentParser(description="Generates release notes for Submitty")
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

    args = parser.parse_args()

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

    type_regex = re.compile(r"^\[([a-zA-Z]+):*([a-zA-Z]*)\].*")
    for commit_obj in commits:
        commit = commit_obj['commit']
        message = commit['message'].splitlines()[0]
        try:
            re_match = re.match(type_regex, message)
            commit_type = re_match.group(1).lower()
            commit_subtype = re_match.group(2).lower()
            if commit_type not in release_commits:
                commit_type = 'bugfix' if commit_subtype == '' else commit_subtype
            elif commit_subtype == 'testing':
                commit_type = 'testing'
        except AttributeError:
            commit_type = "bugfix"
        if commit_type not in release_commits:
            commit_type = 'bugfix'

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
            for commit in release_commits[release_type]['commits']:
                release_notes += f"* {commit}\n"
        release_notes += "\n"

    print(release_notes)


if __name__ == "__main__":
    main()
