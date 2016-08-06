"""Post a HIT to the amazon mturk servers.

This script is adapted from akuznets0v/quickstart-mturk.
"""

import yaml
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications
from boto.mturk.price import Price

# Config variables
DEV_ENVIROMENT_BOOLEAN = True
"""bool: if True, then post the HIT to the mturk sandbox. Otherwise, post to
the live site.
"""

REWARD_AMOUNT = 0
"""float: The dollar amount to give turkers for completing the HIT.
"""

EXPERIMENT_ID = 1
"""int: ID of the experiment you wish to post.
"""


HIT_TITLE = "Dummy title"
"""str: Title for this HIT
"""

HIT_DESCRIPTION = "Dummy description"
"""str: Description for this HIT
"""

HIT_KEYWORDS = ["dummy", "keywords"]
"""list: Keywords for this HIT
"""

HIT_DURATION = 60 * 60
"""int: Duration of this HIT, in seconds
"""

HIT_MAX_ASSIGNMENTS = 15
"""int: Amount of independent copies of the task (turkers can only see one)
"""

QUIZAPP_DOMAIN = "quizapp.tech"
"""str: The domain name for the quizapp instance you wish to use to serve your
HIT
"""


def main():
    """Post a HIT to amazon.
    """
    with open("instance/mturk.yaml") as f:
        config = yaml.load(f)

    # This allows us to specify whether we are pushing to the sandbox or live
    # site.
    if DEV_ENVIROMENT_BOOLEAN:
        AMAZON_HOST = "mechanicalturk.sandbox.amazonaws.com"
    else:
        AMAZON_HOST = "mechanicalturk.amazonaws.com"

    connection = MTurkConnection(
        aws_access_key_id=config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=config["AWS_SECRET_ACCESS_KEY"],
        host=AMAZON_HOST)

    # frame_height in pixels
    frame_height = 800

    # Here, I create two sample qualifications
    qualifications = Qualifications()
    # qualifications.add(PercentAssignmentsApprovedRequirement(
    # comparator="GreaterThan", integer_value="90"))
    # qualifications.add(NumberHitsApprovedRequirement(
    # comparator="GreaterThan", integer_value="100"))

    # This url will be the url of your application, with appropriate GET
    # parameters

    url = "https://{}/mturk/register?experiment_id={}".format(QUIZAPP_DOMAIN,
                                                              EXPERIMENT_ID)
    questionform = ExternalQuestion(url, frame_height)
    create_hit_result = connection.create_hit(
        title=HIT_TITLE,
        description=HIT_DESCRIPTION,
        keywords=HIT_KEYWORDS,
        duration=HIT_DURATION,
        max_assignments=HIT_MAX_ASSIGNMENTS,
        question=questionform,
        reward=Price(amount=REWARD_AMOUNT),
        # Determines information returned by method in API, not super important
        response_groups=('Minimal', 'HITDetail'),
        qualifications=qualifications,
    )
    print "HIT Created."
    print "ID: {}".format(create_hit_result[0].HITId)

if __name__ == "__main__":
    main()
