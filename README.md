Herald
======

Tool to generate the release notes for [Submitty](https://github.com/Submitty/Submitty)
automatically through the GitHub API. Given a tag to go from (defaulting to last release)
and a tag to get to (defaulting to HEAD of master), it rounds up all the commits that have
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
```
