# How to contribute

We welcome pull requests and bug reports!

## Branch structure

Feature development should happen in branches that are forks of the develop
branch. When features are ready to merge, they are merged into develop. When
develop is ready for release, it is merged into master.

For more:

http://nvie.com/posts/a-successful-git-branching-model/

## Testing

In order to run all tests, including linters, run:

    python runtests.py

This will take some time. If you only want to run unit tests:

    py.test tests

This will be much faster. However, `runtests.py` must pass before a change is
merged into develop. Travis CI automatically builds any pull requests.
