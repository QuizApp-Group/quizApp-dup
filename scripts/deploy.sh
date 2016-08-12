#!/bin/bash

# This script is used for deploying to our Digital Ocean droplet
# from Travis CI.

set -x

if [ $TRAVIS_BRANCH == 'develop' ] && [ $TRAVIS_PULL_REQUEST == 'false' ]; then
    # Prepare the deployment key
    chmod 600 deploy_key
    mv deploy_key ~/.ssh/id_rsa

    # Add the server and push
    git remote add deploy "www@104.236.112.220:/home/www/quizApp.git"
    git config user.name "Travis CI"
    git config user.email "alexeibendebury+travis@gmail.com"

    git push --force deploy develop
else
    echo "Not deploying"
fi
