.. _getting_started:

############################
Getting started with QuizApp
############################

**********
Quickstart
**********

Cloning the repository
======================

The first step is to clone the repository onto your disk.

.. code-block:: none

   git clone --branch=master git@github.com:PlasmaSheep/quizApp.git

This will check out the most recent stable version of QuizApp. If you like to
live dangerously and want the bleeding edge version, replace ``master`` with
``develop``.

Installing python dependencies
==============================

It is best practice to install python dependencies using a virtual environment.
This means that the packages that QuizApp installs are independent from any
packages you already have installed, which reduces any possible compatibility
nightmares.

Before continuing, you should follow the installation instructions for
`virtualenvwrapper`_.

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/install.html

Now that you've done that, create a virtual environment for QuizApp. ::

    mkvirtualenv quizApp

Now, in the QuizApp directory, run::

    pip install -r requirements.txt

This will install all requirements necessary for QuizApp to run.

Setting up the database
=======================

Lastly, you need to set up the database. QuizApp uses MariaDB. If you use MySQL
instead of MariaDB, QuizApp should still work normally. If you have neither,
you should `install MariaDB`_.

.. _install MariaDB: https://downloads.mariadb.org/

Once you have MariaDB installed and running, you need to set up the database::

    ./manage.py create-db

You will be prompted for your MySQL root password. This will create a database
called ``quizapp`` and a user named ``quizapp``.

If you would like to have a different username/password combo, edit
``quizApp/config.py``, find the configuration you wish to modify (e.g.
development, production) and modify the variables to your new values. You will
then have to re-run ``create-db``. **Note that your information is not secure
if you do not modify the database username and password.**

.. note::

    ``manage.py`` can handle creation and population of multiple database
    configurations. If you are running a development sever, the above command
    is sufficient. This is because ``manage.py`` defaults to the
    ``development`` configuration.

    If you want to set up a production server, you must specify the
    ``--config`` option::

        ./mange.py --config production create-db

    Keep this in mind when you see other commands using ``manage.py``.


Running QuizApp
===============

This is essentally all you have to do to install QuizApp. To run QuizApp using
the default Flask webserver, simply run::

    ./manage.py run

However, it is not recommended to use this server for production environments.
See :ref:`production_servers` for instructions on running QuizApp in a
production environment.

**************************
Configuration and security
**************************

If you are running quizApp in a production environment, you are definitely
going to want to modify the password of the QuizApp database user for extra
security.  You are maybe going to want to modify the database name or username
that QuizApp uses.

In any case, the easiest method to change the database setup is by modifying
``quizApp/config.py``. There are 3 main environments that QuizApp recognizes -
testing, development, and production. You are probably most interested in
modifying production settings - however note that the ``Production`` class does
not contain any database particulars. This is because database information for
production is stored using  `instance configuration`_.

.. _instance configuration: http://flask.pocoo.org/docs/0.11/config/#instance-folders

In QuizApp, the instance folder is called ``instance``. There is a file there
called ``instance_config.py.ex``. If you wish to override any of the default
production database settings, you should copy this file to
``instance/instance_config.py``.

In that file, there are two primary options. The first option is the database
URI. The full reference for the URI syntax is located `here`_.

.. _here: http://flask.pocoo.org/docs/0.11/config/#instance-folders

The other is the secret key. This is used for various cryptographic purposes
and needs to be randomly generated. Refer to the `flask documentation`_ for
instructions on generating secret keys.

.. _flask documentation: http://flask.pocoo.org/docs/0.11/quickstart/#sessions

In addition, if you plan to use QuizApp with Amazon Mechanical Turk, you will
need to move ``instance/mturk.yaml.ex`` to ``instance/mturk.yaml`` and update
the AWS access key ID and secret key for your mechanical turk user. Remember to
follow best practices and `use IAM`_ for this.

.. _use IAM: https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMechanicalTurkGettingStartedGuide/SetUp.html#create-iam-user-or-role


.. _production_servers:

******************
Production servers
******************

There are many ways to run QuizApp in a server. However, QuizApp is merely a
platform and does not include a web server.

One popular way to run a server is via gunicorn and nginx. Here is a good
`tutorial`_ for setting up that configuration.

.. _tutorial: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04

QuizApp already includes a wsgi file for use with gunicorn, located at
``wsgi.py``.
