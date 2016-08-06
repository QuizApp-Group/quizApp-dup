[![codecov](https://codecov.io/gh/PlasmaSheep/quizApp/branch/develop/graph/badge.svg)](https://codecov.io/gh/PlasmaSheep/quizApp)
[![Documentation Status](https://readthedocs.org/projects/quizapp/badge/?version=latest)](http://quizapp.readthedocs.io/en/latest/?badge=latest)


Platform for asking questions based on visualizations.

## Installation

    pip install -r requirements.txt
    mysql -u root -p < setup_db.sql
    python populate_students_db.py

For more detailed installation instructions, check out the
[documentation](https://quizapp.readthedocs.io/en/latest/getting_started.html).

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
