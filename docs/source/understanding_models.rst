.. _understanding_models:

################################
Understanding the QuizApp models
################################

The structure of a QuizApp database may be confusing at first, but it is
actually fairly understandable. This document focuses on the relationships
between the models. For information about the other fields, view the
documentation for each model.

**********
Experiment
**********

At the root, there is the :py:class:`quizApp.models.Experiment`. An Experiment
contains information such as when to start running, when to stop running, and
any introductory text necessary.

*********************
ParticipantExperiment
*********************

An Experiment also has a collection of
:py:class:`quizApp.models.ParticipantExperiment`. Each ParticipantExperiment
is an association between a :py:class:`quizApp.models.Participant`, an
Experiment, and a collection of :py:class:`quizApp.models.Assignment` s. This
means that in a given Experiment, every Participant will have a different
ParticipantAssignment containing a sequence of Assignments.

**********
Assignment
**********

An Assignment is the object that associates a Participant with an
:py:class:`quizApp.models.Activity`. The reason that ParticipantExperiment does
not directly contain Activities is that Activity is also associated with a
collection of :py:class:`quizApp.models.MediaItem` s. This means that, for the
same Activity, two Participants may see two different Mediaitems. While
performing an Experiment, Participants are shown Assignments in the order they
appear in their ParticipantAssignment class.

********
Activity
********

An Activity is some screen that the Participant sees in the course of an
Experiment. Currently, the only Activity is
:py:class:`quizApp.models.Question`, which displays a Question and some
choices. However, it is possible to extend QuizApp to have other types of
Activities. This would require creating a subclass of Activity in `models.py`
and implementing the correct logic to handle creation, reading, and updating of
your new Activity type.

========
Question
========

There are several subclasses of Question. They all operate around the principle
of displaying a string of text, followed by a series of
:py:class:`quizApp.models.Choice` s. Each Choice is related to only one
Question, so Choices are not recycled from Question to Question. Since each
Choice has its own `correct` field, you can have a Question with all correct
choices, no correct choices, or anywhere in between. Questions are also
associated with Datasets. This represents which Datasets a Question's
MediaItems are drawn from. A Question not associated with any Datasets can draw
MediaItems from any dataset.

*********
MediaItem
*********

A MediaItem is some stimulus that should be displayed when a Participant is
doing an Activity. Each MediaItem is associated with a
:py:class:`quizApp.models.Dataset`. By default, QuizApp contains the
:py:class:`quizApp.models.Graph` MediaItem. A Graph is simply an image file
located on disk. Again, it is possible to expand QuizApp to have MediaItems
that are videos, sounds, or anything else. You would need to subclass
MediaItem, then implement the correct logic for rendering the new MediaItem
type.

*******
Dataset
*******

A Dataset represents a collection of MediaItems that come from a common source.
