#!/bin/bash

set -x

if [ $TRAVIS_BRANCH == 'develop' ] ; then
    chmod 600 deploy_key

    mv deploy_key ~/.ssh/id_rsa

    git remote add deploy "www@104.236.112.220:/home/www/quizApp.git"
    git config user.name "Travis CI"
    git config user.email "alexeibendebury+travis@gmail.com"

    git push --force deploy develop
else
    echo "Not deploying"
fi
