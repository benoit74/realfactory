#!/usr/bin/python3

from gitlab import Gitlab
from raspberry import Raspberry
import signal
import time
import sys
import traceback

class GracefulKiller:
    kill_now = False
    def __init__(self, gitlab):
        self.gitlab = gitlab
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print("Signal received")
        self.gitlab.exit_gracefully()
        self.kill_now = True

if __name__ == '__main__':

    rpi = Raspberry()
    gitlab = Gitlab(rpi)
    killer = GracefulKiller(gitlab)

    while True:
        if killer.kill_now:
            break
            
        print('---')
        print('Updating state')
        try:
            gitlab.update_state()
        except:
            print("Unexpected error:")
            traceback.print_exc()

        if killer.kill_now:
            break

        print('Sleeping few secs')
        time.sleep(5)
    
    print("End of the program. I was killed gracefully :)")