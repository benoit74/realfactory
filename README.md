[photo_udd]: https://www.oviles.info/ci_for_real.png "A real CI"
[schema_hardware]: https://www.oviles.info/ci_hardware.png "Hardware schematic"
[resin.io]: https://resin.io/ "Resin.io website"

# A real software factory
![Photo of the real CI][photo_udd]

This folder contain a Python 'application' to bring to life a real CI/CD model.

This code is meant to be run on the RaspberryPi inside the prototype on the picture above.

It is configured to track the stack of a Gitlab project pipelines and react to events on this pipeline.

This application is meant to be deployed on the Pi through Resin.io

## Application

The application is composed of :
- *gitlab.py*: a kind a state machine, responsible of finding the last running pipeline, the jobs, and call for physical actions (smoke and sounds)
- *raspberry.py*: the real implementation of physical actions, including cleanup at application exit.
- *main.py*: the real application, looping forever until SIGINT or SIGKILL are received (launches the cleanup).

Most of the code  (**all business logic code indeed**) is unit-tested in *test_main.py*.

## Environment variables

Some environment variables are mandatory for the code to execute:
- GITLAB_TOKEN : access token to connect to Gitlab API to retrieve pipelines and jobs from Gitlab
- PROJECT_ID : Gitlab project ID (visible in the project details page for instance)

## Deployment on Resin.io

This code can (and should) be deployed to the Raspberry Pi with [Resin.io][resin.io].
All required files are present in this repo:
- *Dockerfile.template*: template of the Dockerfile to build the Resin.io container
- *requirements.txt*: list of pip packages to install for the application to run

## Hardware

The model is composed of a Raspberry Pi, a modelling chimney emiting smoke when powered-on and some electronics to make all this work together.

In order to simplify the demo of the factory, the model is powered up by a simple laptop adapter delivering 19.5V CC- 3.33A. This is enough to power the Pi + the chimney resistor. The most complex part was to find the matching connector to plug the adapter into the model in an industrialised manner.

However, a voltage adapter is needed to reduce the voltage for the Pi and a transistor with a current limiting resistor is needed to avoid draining too much current out of the Raspberry Pi GPIO when powering-up the chimney (it consumes around 40mA while the Pi GPIO is limited to 16mA per pin).

The final electronic schema is the following one (details of the voltage adapter and the Raspberry Pi are not provided for simplicity).

![Schema of the Hardware][schema_hardware]

## Change sound volume

In order model, the sound is emitted by a tiny USB speaker. It's volume can be adjusted in the application container (if deployed on resin.io) with alsamixer

1. Log to the application container (*main* obviously)
1. Run _alsamixer_
1. Select sound card number 1 : F6
1. Up/Down arrow to change the level
1. Esc to save and quit the utility
