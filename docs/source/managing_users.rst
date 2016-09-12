.. _managing_users:

##############
Managing users
##############

Managing users is fairly straightforward with ``manage.py``. The relevant
commands are ``manage.py create-user`` and ``mange.py delete-user``. Remember
that ``--help`` will give information about possible command line options.

Here are some examples:

1. Create a new participant with the username ``username`` and password
   ``password``::

    ./manage.py create-user --role participant --email username --password password

2. Create a new experimenter with the username ``username`` and password
   ``password``::

    ./manage.py create-user --role experimenter --email username --password password

3. Delete a user with the username ``username``::

    ./manage.py delete-user --username username
