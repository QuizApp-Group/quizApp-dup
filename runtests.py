#!/usr/bin/env python
"""Run py.test on this project.
"""

import os
import sys

import pytest


def runtests():
    """Set the app config to testing and run pytest, passing along command
    line args.
    """
    os.environ["APP_CONFIG"] = "testing"
    return pytest.main(["--cov=quizApp",
                        "--flake8",
                        "--pylint",
                        "--ignore=venv",
                        "./"] + sys.argv)

if __name__ == "__main__":
    exit(runtests())
