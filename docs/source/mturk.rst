.. _mturk:

#########################################
Using QuizApp with Amazon Mechanical Turk
#########################################

1. Modify ``instance/mturk.yaml`` to correspond to your AWS credentials

2. Modify the config variables in the start of the file to your desired
   settings

3. Run ``./manage.py post-hits --experiment-id <experiment_id>`` with the
   ID of the experiment you wish to post.

4. If you are successful, you will see the message "HIT Created" followed by
   the ID of the HIT. You should now be able to see them in the requester
   interface on mechanical turk.

Further information on using the ``post-hits`` option can be found by doing
``./manage.py post-hits --help``.
