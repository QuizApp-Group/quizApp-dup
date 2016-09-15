#!/bin/bash

# This script is used for deploying to our Digital Ocean droplet
# from Travis CI.

set -x

# note that we specify the python version - this is because we are running
# tests for 2 and 3, but we only want to deploy once per travis build.
if [ $TRAVIS_BRANCH == 'master' ] && [ $TRAVIS_PULL_REQUEST == 'false' ] &&
    [ $TRAVIS_PYTHON_VERSION == '2.7' ]; then
    # Prepare the deployment key
    chmod 600 deploy_key
    mv deploy_key ~/.ssh/id_rsa

    # Add the server and push
    git remote add deploy "www@quizapp.tech:/home/www/quizApp.git"
    git config user.name "Travis CI"
    git config user.email "alexeibendebury+travis@gmail.com"

    git push --force deploy master
else
    echo "Not deploying"
fi
