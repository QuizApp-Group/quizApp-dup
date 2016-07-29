"""Various helper methods for tests.
"""

import json


def json_success(json_string):
    """Assert that this json string contains a top level item called "success"
    and it is set to 1.
    """
    return json.loads(json_string)["success"] == 1
