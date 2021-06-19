Herald
======

Tool to generate the release notes for [Submitty](https://github.com/Submitty/Submitty)
automatically through the GitHub API. Given a tag to go from (defaulting to last release)
and a tag to get to (defaulting to HEAD of main), it rounds up all the commits that have
been made and organizes them into a nice list.

Requirements
------------
* Python 3.6+
* [requests](https://pypi.org/project/requests/) (`pip3 install requests`)

Usage
-----
```
$ python3 herald.py
$ ./herald.py
$ ./herald.py --help
usage: herald.py [-h] [--version] [--from FROM_TAG] [--to TO_TAG] [repo]

Generates release notes for Submitty

positional arguments:
  repo             Repository to generate notes for

optional arguments:
  -h, --help       show this help message and exit
  --version        show program's version number and exit
  --from FROM_TAG  Set release tag to compare from. Defaults to last release.
  --to TO_TAG      Set release to compare to. Defaults to HEAD of main.
```
