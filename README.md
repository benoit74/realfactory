[photo_udd]: https://www.oviles.info/ci_for_real.png "A real CI"

# Code for physical CI/CD
![Photo of the real CI][photo_udd]

This folder contain a Python 'application' to bring to life a real CI/CD.

This code is meant to be run on the RaspberryPi inside the prototype on the picture above.

It is configured to track the stack of the Gitlab cff_poc pipelines and react to events on this pipeline.

This application is deployed on the Pi through Resin.io


## Set sound volume

1. Log to raspberry
1. Run _sudo alsamixer_
1. Select sound card number 1 : F6
1. Up/Down arrow to chnage the level
1. Esc to save


## Application

The application is composed of :
- *gitlab.py*: a kind a state machine, responsible of finding the last running pipeline, the jobs, and call for physical actions (smoke and sounds)
- *raspberry.py*: the real implementation of physical actions, including cleanup at application exit.
- *main.py*: the real application, looping forever until SIGINT or SIGKILL are received (launches the cleanup).

Most of the code  (**all business logic code indeed**) is unit-tested in *test_main.py*.

## Environment variables

- GITLAB_TOKEN : access token to connect to Gitlab API to retrieve pipelines and jobs from Gitlab
- PROJECT_ID : Gitlab project ID (visible in the project details page for instance)

## Resin.io

TODO

## Deployment

TODO