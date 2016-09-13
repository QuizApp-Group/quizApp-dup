.. _import_export:

############################
Importing and exporting data
############################

The primary way of importing and exporting data is through the ``/data/manage``
page. There are two operations you can do on this page: importing and
exporting.

*********
Exporting
*********

To export a dump of all data in the database, click on the `Export` link.
Alternatively, you can visit the ``/data/export`` page. This will take some
time due to the amount of database queries and processing, but it will give you
all the data in the database in spreadsheet form. The tab names correspond to
the types of objects in the database, and the column headers are in the format
``<table_name>:<database_column_name>``. Each row in every tab represents one
database record.

*********
Importing
*********

To import data into the database, you must first fill out a spreadsheet in a
particular way. First click on the "Download Template" link. This template
represents the type of spreadsheet that the import interface is expecting. On
the first tab is some brief documentation. The other tabs are ordered from
parent to child, such that children specify their parents. The general idea is
such:

* Do not modify the first row (column headers) of any sheet
* All information that you add must be added under the headers
* Some fields are relations, and some relations link to multiple objects (these
  are called one to many or many to many).

  * For one to one relations, enter the ``id`` of the object you want to link
    to. For example, if you want to associate an AssignmentSet with a specific
    Experiment, in the ``assignment_set:experiment`` column you should have the
    value of the ``experiment:id`` column of the Experiment you want to link
    to.
  * For one to many or many to many relations, you should have a comma
    separated list of IDs. You can find the IDs the same way you did for one to
    one relations.

You may be asking where you find the IDs for your associations. There are two
possibilities here.

1. You want to relate an object you are importing with another object you are
   importing (e.g. you are creating an AssignmentSet in your import sheet and
   want to associate an Assignment you are creating with it).

   In this case, you must assign the Assignment some id in the
   ``assignment:id`` column. The value of this ID is not strictly important, as
   long as it is unique in this spreadsheet. Then, in the
   ``assignment_set:assignment`` column, enter the ID of the Assignments you
   want to associate with - remember that since this is a one to many relation
   you would enter multiple Assignments as comma separated IDs.

2. You want to relate an object you are importing with an object already in the
   database (e.g. you are creating a AssignmentSet and you want to add
   it to an existing Experiment).

   In this case, you must look up the ID of the experiment in the export sheet
   or in the web interface in the table that lists experiments.  Then, you may
   put that id in the ``assignment_set:experiment`` column in your import
   sheet.

For a general overview of how the models work, refer to
:ref:`understanding_models`. For a detailed documentation of the models and
their fields (which correspond to the columns in the spreadsheet), refer to
:py:mod:`quizApp.models`.
