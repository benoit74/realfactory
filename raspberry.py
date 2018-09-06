from subprocess import call
import os

class Raspberry:

    def __init__(self, run_rpi = True):
        self.run_rpi = run_rpi
        if (run_rpi):
            print('Initialising GPIO')
            import RPi.GPIO as GPIO # pylint: disable=E0401      
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(21, GPIO.OUT)

    def set_pin_state(self, state):
        self.pin_state = state
        if (self.run_rpi):
            print('Updating pin state: up={}'.format(state))
            import RPi.GPIO as GPIO # pylint: disable=E0401  
            if (state):
                GPIO.output(21, GPIO.HIGH) # pylint: disable=E0602
            else:
                GPIO.output(21, GPIO.LOW) # pylint: disable=E0602

    def play_sound(self, name):
        if (self.run_rpi):
            print('Playing sound {}'.format(name))
            call(["aplay", "-D", "plughw:1,0", os.path.dirname(os.path.abspath(__file__)) + "/resources/mario/" + name + ".wav"])

    def play_pipeline_start(self):
        self.play_sound('pipeline_start')

    def play_unit_tests_completed(self):
        self.play_sound('unit_tests_completed')

    def play_build_completed(self):
        self.play_sound('build_completed')

    def play_package_completed(self):
        self.play_sound('package_completed')

    def play_deploy_completed(self):
        self.play_sound('deploy_completed')

    def play_pipeline_completed(self):
        self.play_sound('pipeline_completed')

    def play_pipeline_failed(self):
        self.play_sound('pipeline_failed')

    def exit_gracefully(self):
        if (self.run_rpi):
            print('RPi exiting gracefully')
            self.set_pin_state(False)
            import RPi.GPIO as GPIO # pylint: disable=E0401  
            GPIO.cleanup() # pylint: disable=E0602
