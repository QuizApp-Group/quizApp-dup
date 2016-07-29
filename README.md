[![codecov](https://codecov.io/gh/PlasmaSheep/quizApp/branch/develop/graph/badge.svg)](https://codecov.io/gh/PlasmaSheep/quizApp)

Platform for asking questions based on visualizations.

## Installation

    pip install -r requirements.txt
    mysql -u root -p < setup_db.sql
    python populate_students_db.py

## A note on production environments

In order to run this application on a production environment, you must do two
things.

1. Set the `APP_CONFIG` environment variable to `production`

2. Copy the `instance/instance_config.py.ex` file to `instance/instance_config.py` and modify
    the `SECRET_KEY` and `SQLALCHEMY_DATABASE_URI` to suitable values.

## Running

    python runserver.py

## Using

After running the code, it should tell you where it is running. You can
then navigate to this address in a browser to use the quiz platform.

## Testing

    ./runtests.sh

## Branches

- `master`: This branch contains stable releases of the code.

- `develop`: Feature development and as-yet untested code lives in
    this branch before it is merged into `master`.
