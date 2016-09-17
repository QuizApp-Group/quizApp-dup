.. _import_export:

############################
Importing and exporting data
############################

After creating your experiment, activities, media items, and datasets, you must
set up your assignment sets and assignments to begin an experiment. Setting up
your assignment sets and assignments is referred to as "importing data". Due to
the diversity of methods for assigning assignments, quizApp does not provide a
GUI but does allow a lot of flexibility. Once an experiment has been run, you
will want to export your data to analyze responses. The primary way of
importing and exporting data is through the ``/data/manage`` page. There are
two operations you can do on this page: importing and exporting.

*********
Exporting
*********

All data
========

To export a dump of all data in the database, click on the `Export` link.
Alternatively, you can visit the ``/data/export`` page. This will take some
time due to the amount of database queries and processing, but it will give you
all the data in the database in spreadsheet form. The tab names correspond to
the types of objects in the database, and the column headers are in the format
``<table_name>:<database_column_name>``. Each row in every tab represents one
database record.

One experiment's data
=====================

To export just the data from one experiment, you can use the
``/experiments/<id>/results`` page. There is a link there titled `Export to
XLSX`. Clicking on this link will download a summary of answers to this
experiment. Each assignment set will have its own row, and each assignment in
that assignment set will have three columns:

1. A string representation of that activity, e.g. the question text. The
   contents of this row is a string representation of the result for this
   activity prepended with the assignment ID - so for example, the header might
   be the question text and each cell under the header would be a participant's
   answer (prepended with the ID of the assignment itself).
2. Correct/incorrect, with each cell below that being ``TRUE`` or ``FALSE``
3. Number of points awarded for the result

If a participant did not answer a question present in their assignment set, the
token ``_BLANK_`` will be present to indicate this.


*********
Importing
*********

To import data into the database, you must modify a script provided with
quizApp, namely ``scripts/generate_import_sheet.py``. There are two variables
you are going to be interested in, both defined in the beginning of the file:

1. ``DEST_FILE``: The name of the output file
2. ``DATA``: A list containing the actual data that should be written to the
   spreadsheet

``DEST_FILE`` is self explanatory, and ``DATA`` has comments above it
documenting its format. Note that you must know the IDs of the experiments,
activities, and media items you are interested in using. You can find them in
the export spreadsheet or in the web interface.

Once you have specified your ``DATA`` variable, you can simply run
``./generate_import_sheet.py`` (make sure you are in your quizApp virtual
environment). There will be a file in the current directory named based on
``DEST_FILE``, and by uploading this spreadsheet in ``/data/manage`` your
experiment will be populated with assignments and ready for use.

Note that there is no discovery mechanism for participants to find experiments
- the experiment URL must be provided to the participants, which can be found
on the experiments settings page.

For a general overview of how the models work, refer to
:ref:`understanding_models`. For a detailed documentation of the models and
their fields (which correspond to the columns in the spreadsheet), refer to
:py:mod:`quizApp.models`.
