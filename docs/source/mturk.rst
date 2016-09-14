.. _mturk:

#########################################
Using QuizApp with Amazon Mechanical Turk
#########################################

QuizApp includes a small script which allows you to post an Experiment as a HIT
on Amazon Mechanical Turk. Using the script is fairly straightforward:

1. Modify ``instance/mturk.yaml`` to correspond to your AWS credentials

2. Run ``./manage.py post-hits --experiment-id <experiment_id>`` with the
   ID of the experiment you wish to post.

   .. note::

      Make sure you are still in the virtual environment you made previously:
      ``workon quizApp``

3. If you are successful, you will see the message "HIT Created" followed by
   the ID of the HIT. You should now be able to see them in the requester
   interface on mechanical turk.

   .. note::

      This only creates the HIT in the amazon turk sandbox. If you wish to post
      it in the production environment, you must specify ``--live`` on the
      command line.

Further information on using the ``post-hits`` subcommand can be found by doing
``./manage.py post-hits --help``.
