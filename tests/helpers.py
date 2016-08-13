"""Various helper methods for tests.
"""
from __future__ import unicode_literals

import json


def json_success(json_bytes):
    """Assert that this json string contains a top level item called "success"
    and it is set to 1.
    """
    return json.loads(json_bytes.decode("utf-8"))["success"] == 1
