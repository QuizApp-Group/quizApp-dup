.. _understanding_quizapp:

###################################
Understanding the QuizApp structure
###################################

There are 3 principle parts of the quizApp system: the experiments, activities,
and datasets. The experiment components handle tasks related to rendering,
running, and updating experiments - this includes showing assignments to
participants, saving their answers, generating experiment reports, and more.
Activities is concerned primarily with rendering and managing activities.
Datasets is primarily concerned with managing datasets as well as rendering and
managing activities. Most components of quizApp are divided along these broad
lines.

As far as application logic goes, quizApp follows a fairly typical MVC design
pattern. The ``quizApp/`` directory is organized like so:

- ``forms``: Contains logic used for rendering and validating forms
- ``static``: Contains static files, like graphs, css, and js
- ``templates``: Contains template files, which specify what is displayed to
  the users and in what format
- ``views``: Contains view logic that interfaces with the models and sends data
  to templates for rendering
- ``models.py``: Database models that specify how information is stored in the
  database and take care of validation. More information about models is
  available in :ref:`understanding_models`.
- ``filters.py``: Various jinja filters that are used for formatting and
  rendering purposes
- ``__init__.py``: File that handles setup and initialization of the
  application

************
QuizApp Flow
************

In general, each view file registers a number of URLs that are handled by some
function in the view file. When a user makes a request to a certain endpoint,
the view function first checks authentication, then validates the URL (if
applicable, e.g. checking to make sure the requested experiment exists),
accesses the database (if necessary), performs any necessary processing, then
sends some context variables to a template, which is rendered and shown to the
user.

When it comes to running experiments, participants must first be given a link
to the experiment itself. Once they arrive at the landing page, they will see
the experiment's blurb and be assigned an assignment set. Once they click
"start" they will begin the first assignment in their set. Each assignment will
be rendered as its media items followed by its activity. The participant's
response will be stored as a Result object on the Assignment. Once the
participant finalizes their responses, their assignment set will be marked as
completed and they will be unable to run the experiment again.
