"""Post a HIT to the amazon mturk servers.

This script is adapted from akuznets0v/quickstart-mturk.
"""

import yaml
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications
from boto.mturk.price import Price


QUIZAPP_DOMAIN = "quizapp.tech"
"""str: The domain name for the quizapp instance you wish to use to serve your
HIT
"""


def post_hits(max_assignments, duration, keywords, description, title,
              experiment_id, reward, live):
    """Post a HIT to amazon.
    """
    with open("instance/mturk.yaml") as f:
        config = yaml.load(f)

    # This allows us to specify whether we are pushing to the sandbox or live
    # site.
    if not live:
        AMAZON_HOST = "mechanicalturk.sandbox.amazonaws.com"
    else:
        AMAZON_HOST = "mechanicalturk.amazonaws.com"

    connection = MTurkConnection(
        aws_access_key_id=config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=config["AWS_SECRET_ACCESS_KEY"],
        host=AMAZON_HOST)

    # Here, I create two sample qualifications
    qualifications = Qualifications()
    # qualifications.add(PercentAssignmentsApprovedRequirement(
    # comparator="GreaterThan", integer_value="90"))
    # qualifications.add(NumberHitsApprovedRequirement(
    # comparator="GreaterThan", integer_value="100"))

    # The first argument is the URL that turkers will be sent to, and the
    # second argument is the frame height in pixels
    questionform = ExternalQuestion(
        "https://{}/mturk/register?experiment_id={}".format(QUIZAPP_DOMAIN,
                                                            experiment_id),
        800
    )
    create_hit_result = connection.create_hit(
        title=title,
        description=description,
        keywords=keywords,
        duration=duration,
        max_assignments=max_assignments,
        question=questionform,
        reward=Price(amount=reward),
        # Determines information returned by method in API, not super important
        response_groups=('Minimal', 'HITDetail'),
        qualifications=qualifications,
    )
    print "HIT Created."
    print "ID: {}".format(create_hit_result[0].HITId)
