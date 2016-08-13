#!/bin/env python2

"""Using excel files, populate the database with some placeholder data.
"""
from __future__ import print_function
from datetime import datetime, timedelta
import os
import csv
import random

from flask_security.utils import encrypt_password

from scripts.clear_db import clear_db
from quizApp.models import Question, Assignment, ParticipantExperiment, \
    Participant, Graph, Experiment, Dataset, Choice
from quizApp import db, security
from quizApp.config import basedir

# In this list, each list is associated with a participant (one to one).  The
# first three tuples in each list are associated with training questions.  The
# last three tuples in each list are associated with pre/post questions.  In
# each tuple, the first number represents the dataset of the question.  The
# second number is associated with the ID of the graph. TODO: simplify this
# relationship.  The order of the tuples along with the participant id gives
# the participant test id.  Note: No participant has two tuples with the same
# dataset - this means the relationship between participant test and dataset is
# many to one.

PARTICIPANT_QUESTION_LIST = \
    [[(1, 2), (3, 2), (4, 0), (2, 1), (5, 0), (0, 0)],
     [(1, 2), (0, 2), (5, 1), (2, 0), (3, 0), (4, 1)],
     [(3, 0), (2, 1), (4, 0), (5, 1), (0, 0), (1, 2)],
     [(5, 2), (2, 2), (0, 1), (1, 0), (3, 1), (4, 0)],
     [(2, 2), (0, 1), (3, 1), (4, 0), (1, 1), (5, 1)],
     [(0, 0), (3, 0), (1, 0), (2, 2), (5, 2), (4, 2)],
     [(4, 2), (1, 1), (5, 2), (0, 0), (3, 1), (2, 1)],
     [(4, 2), (3, 0), (1, 2), (0, 1), (5, 2), (2, 1)],
     [(3, 1), (2, 0), (4, 2), (1, 1), (0, 1), (5, 2)],
     [(0, 2), (4, 1), (3, 0), (5, 0), (1, 1), (2, 0)],
     [(5, 1), (4, 1), (0, 2), (3, 2), (1, 2), (2, 0)],
     [(2, 1), (5, 0), (0, 2), (3, 2), (4, 2), (1, 1)],
     [(3, 1), (5, 2), (4, 1), (0, 2), (2, 0), (1, 0)],
     [(1, 1), (5, 1), (2, 2), (4, 0), (3, 1), (0, 2)],
     [(2, 0), (1, 0), (5, 0), (4, 1), (0, 2), (3, 2)],
     [(1, 1), (5, 1), (0, 2), (4, 2), (2, 1), (3, 1)],
     [(5, 1), (4, 2), (2, 0), (1, 2), (3, 2), (0, 1)],
     [(0, 0), (2, 2), (1, 0), (4, 1), (5, 2), (3, 2)],
     [(0, 1), (1, 2), (5, 2), (2, 0), (4, 2), (3, 0)],
     [(1, 0), (3, 2), (0, 0), (2, 2), (4, 0), (5, 0)],
     [(3, 2), (2, 1), (4, 1), (1, 0), (5, 1), (0, 0)],
     [(1, 0), (3, 2), (5, 0), (0, 1), (4, 1), (2, 2)],
     [(5, 2), (3, 1), (1, 1), (0, 0), (4, 0), (2, 2)],
     [(4, 1), (0, 0), (3, 1), (2, 1), (5, 1), (1, 0)],
     [(5, 0), (2, 0), (0, 1), (3, 0), (1, 1), (4, 2)],
     [(0, 2), (4, 0), (1, 1), (3, 1), (2, 2), (5, 0)],
     [(2, 0), (0, 0), (3, 0), (1, 2), (5, 0), (4, 1)],
     [(0, 1), (4, 2), (2, 1), (5, 2), (1, 0), (3, 0)],
     [(5, 0), (4, 0), (2, 2), (3, 0), (1, 2), (0, 1)],
     [(4, 0), (1, 2), (2, 1), (5, 1), (0, 2), (3, 2)]]

GRAPH_ROOT = "static/graphs"
DATA_ROOT = "data/"
QUESTION_TYPE_MAPPING = {"multiple_choice": "question_mc_singleselect",
                         "heuristic": "question_mc_singleselect_scale",
                         "rating": "question_mc_singleselect_scale",
                         "pre_test": "question"}


def randomize_scorecard_settings(scorecard):
    """Generate some random data for this scorecard
    """
    settings = ["display_scorecard", "display_score", "display_correctness",
                "display_time", "display_feedback"]

    for setting in settings:
        setattr(scorecard, setting, bool(random.getrandbits(1)))


def get_experiments():
    """Populate the database with initial experiments.
    """
    blurb = ("You will be asked to respond to a series of multiple choice"
             " questions regarding various graphs and visualizations.")

    pre_test = Experiment(name="Pretest",
                          blurb=blurb,
                          disable_previous=True,
                          show_timers=True,
                          show_scores=True,
                          start=datetime.now(),
                          stop=datetime.now() + timedelta(days=3))
    pre_test.scorecard_settings.display_scorecard = True
    pre_test.scorecard_settings.display_score = True
    pre_test.scorecard_settings.display_correctness = True
    pre_test.scorecard_settings.display_time = True
    pre_test.scorecard_settings.display_feedback = True

    test = Experiment(name="Main test",
                      blurb=blurb,
                      start=datetime.now(),
                      stop=datetime.now() + timedelta(days=5))

    post_test = Experiment(name="Post-test",
                           blurb=blurb,
                           start=datetime.now() + timedelta(days=-3),
                           stop=datetime.now())

    db.session.add(pre_test)
    db.session.add(test)
    db.session.add(post_test)


def get_questions():
    """Populate the database with questions based on csv files.
    """
    categories = ["foobar", "foo", "example", "baz"]
    with open(os.path.join(DATA_ROOT, "questions.csv")) as questions_csv:
        question_reader = csv.DictReader(questions_csv)
        for row in question_reader:
            # Convert from 0 indexed to 1 indexed
            dataset_id = int(row["dataset_id"]) + 1
            dataset = Dataset.query.get(dataset_id)

            includes_explanation = int(random.random() * 10) % 2
            needs_comment = int(random.random() * 10) % 2

            if not dataset:
                dataset = Dataset(
                    id=dataset_id,
                    name=row["Dataset Nickname"]
                )
                db.session.add(dataset)

            explanation = ""
            if includes_explanation:
                explanation = "This explains question " + \
                    str(row["question_id"])

            if QUESTION_TYPE_MAPPING[row["question_type"]] == "question":
                continue

            question = Question(
                id=row["question_id"],
                datasets=[dataset],
                question=row["question_text"],
                type=QUESTION_TYPE_MAPPING[row["question_type"]],
                explanation=explanation,
                num_media_items=1,
                category=random.choice(categories),
                needs_comment=needs_comment)
            randomize_scorecard_settings(question.scorecard_settings)

            if "scale" in question.type:
                for i in range(1, 6):
                    choice = ""
                    if i == 1:
                        choice = "Very bad"
                    elif i == 3:
                        choice = "Neutral"
                    elif i == 5:
                        choice = "Very good"

                    question.choices.append(
                        Choice(choice=choice,
                               label=str(i),
                               points=1,
                               correct=True))

            db.session.add(question)


def get_choices():
    """Populate the database with choices based on csv files.
    """
    with open(os.path.join(DATA_ROOT, "choices.csv")) as choices_csv:
        choice_reader = csv.DictReader(choices_csv)
        for row in choice_reader:
            choice = Choice(
                points=1,
                question_id=row["question_id"],
                choice=row["answer_text"],
                correct=row["correct"] == "yes",
                label=row["answer_letter"])
            if choice.correct:
                choice.points = random.choice(range(1, 5))
            db.session.add(choice)
    with open(os.path.join(DATA_ROOT, 'graph_table.csv')) as graphs_csv:
        graphs = csv.DictReader(graphs_csv)

        for graph in graphs:
            graph = Graph(
                id=graph["graph_id"],
                dataset_id=int(graph["dataset"])+1,
                flash=bool(random.getrandbits(1)),
                flash_duration=random.randint(500, 1500),
                path=os.path.join(basedir, GRAPH_ROOT,
                                  graph["graph_location"]))
            db.session.add(graph)


def create_participant(pid):
    """Given an ID number, create a participant record, adding them to each
    of the given experiments.
    """
    participant = Participant(
        id=pid,
        email=str(pid),
        password=encrypt_password(str(pid)),
        opt_in=False,
        active=True,
    )
    security.datastore.add_role_to_user(participant, "participant")
    db.session.add(participant)


def get_students():
    """Get a list of students from csv files.
    """
    security.datastore.create_role(name="participant")
    security.datastore.create_role(name="experimenter")
    participant_list_file = os.path.join(DATA_ROOT,
                                         "participant_id_list.csv")

    with open(participant_list_file) as participants_csv:
        participant_reader = csv.DictReader(participants_csv)
        for row in participant_reader:
            questions_id = row["Questions"]
            heuristics_id = row["Heuristics"]

            if questions_id:
                create_participant(questions_id)

            if heuristics_id:
                create_participant(heuristics_id)

    security.datastore.create_user(
        email="experimenter@example.com",
        password=encrypt_password("foobar"),
        active=True,
        roles=["experimenter"]
    )


def create_participant_data(participant_question_list, test, group):
    """
    sid_list: list of participant id's
    participant_question_list: magic list of lists of tuples
    test: pre_test or training or post_test
    group: question or heuristic
    """
    experiments = {
        "pre_test": Experiment.query.filter_by(name="Pretest").one(),
        "test": Experiment.query.filter_by(name="Main test").one(),
        "post_test": Experiment.query.filter_by(name="Post-test").one()
    }

    if test == 'pre_test' or test == 'post_test':
        question_list = [x[:3] for x in participant_question_list]
    else:
        # pick last three
        question_list = [x[3:] for x in participant_question_list]

    for participant in question_list:
        participant_experiment = ParticipantExperiment(
            experiment=experiments[test])
        db.session.add(participant_experiment)

        for graph in participant:
            dataset = graph[0]
            graph_id = int(str(dataset)+str(graph[1]+1))
            if test == 'pre_test' or test == 'post_test':
                question_id = int(str(dataset)+str(5))
                create_assignment(question_id,
                                  experiments[test],
                                  participant_experiment, graph_id)

            else:  # training
                if group == 'heuristic':
                    dataset_range = range(5, 9)

                else:
                    dataset_range = range(1, 5)

                for x in dataset_range:
                    question_id = int(str(dataset)+str(x))
                    # write row to db
                    create_assignment(question_id,
                                      experiments[test],
                                      participant_experiment, graph_id)

    print("Completed storing {} {} tests".format(test, group))


def create_assignment(question_id, experiment,
                      participant_experiment, graph_id):
    """Given parameters, create an assignment, returning without doing anything
    if the question doesn't exist.
    """
    question = Question.query.get(question_id)
    if not question:
        return
    question.experiments.append(experiment)

    assignment = Assignment(
        experiment=experiment,
        participant=participant_experiment.participant,
        media_items=[Graph.query.get(graph_id)])
    assignment.activity = question
    assignment.participant_experiment = participant_experiment

    experiment.activities.append(
        Question.query.get(question_id))

    db.session.add(assignment)


def create_assignments():
    """Create all necessary assignments/ParticipantExperiments.
    """
    for test in ['pre_test', 'test', 'post_test']:
        create_participant_data(PARTICIPANT_QUESTION_LIST, test, 'question')
        create_participant_data(PARTICIPANT_QUESTION_LIST, test, 'heuristic')


def setup_db():
    """Clear the database, then populate it using default data.
    """
    # There needs to be an app context for this to run.
    clear_db()
    get_experiments()
    get_questions()
    get_choices()
    get_students()
    create_assignments()

    db.session.commit()


if __name__ == "__main__":
    setup_db()
