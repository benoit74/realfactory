from raspberry import Raspberry             
import requests
from secret import *
from functools import reduce
import os

PROJECT_ID = '5885481'
BASE_URL = 'https://gitlab.com/api/v4'
GET_PROJECT = BASE_URL + '/projects/' + PROJECT_ID
GET_PIPELINES = BASE_URL + '/projects/' + PROJECT_ID + '/pipelines'

UNIT_TEST_JOBS_COUNT = 3
BUILD_JOBS_COUNT = 1
DOCKER_PACKAGE_JOBS_COUNT = 3
DEPLOY_JOBS_COUNT = 1

HEADERS = {'Private-Token': os.environ['GITLAB_TOKEN']}

class Gitlab:

    def __init__(self, raspberry):
        self.global_state = 'NOT_INITIALIZED'
        self.raspberry = raspberry
    
    # EXIT of program has been request (SIGINT or SIGTERM typically)
    def exit_gracefully(self):
        self.raspberry.exit_gracefully()
    
    # function to call regularly to update state (and perform 'real life' actions)
    def update_state(self):
        print("Current global state: {}".format(self.global_state))
        if (self.global_state == 'NOT_INITIALIZED'):
            print("global_state: NOT_INITIALIZED -> WAITING")
            self.raspberry.set_pin_state(False)
            self.global_state = 'WAITING'
        elif (self.global_state == 'WAITING'):
            self.pipeline = self.__get_last_pipeline()
            print('last pipeline id={} status={}'.format(self.pipeline['id'],self.pipeline['status']))
            if (self.pipeline['status'] == 'running'):
                print("global_state: WAITING -> RUNNING")
                self.raspberry.set_pin_state(True)
                self.raspberry.play_pipeline_start()
                self.global_state = 'RUNNING'
                self.pipeline_state = 'UNIT_TESTS'
        elif (self.global_state == 'RUNNING'):
            self.pipeline = self.get_single_pipeline()
            if (self.pipeline['status'] == 'failed'):
                print("global_state: RUNNING -> WAITING (failed)")
                self.raspberry.set_pin_state(False)
                self.raspberry.play_pipeline_failed()
                self.global_state = 'WAITING'
            elif (self.pipeline['status'] == 'success'):
                print("global_state: RUNNING -> WAITING (success)")
                self.raspberry.set_pin_state(False)
                self.raspberry.play_pipeline_completed()
                self.global_state = 'WAITING'
            elif (self.pipeline['status'] == 'running'):
                print("Current pipeline state: {}".format(self.pipeline_state))
                jobs = self.get_jobs_from_pipeline()
                if (self.pipeline_state == 'UNIT_TESTS'):
                    nb_unit_tests_completed = len(list(filter(lambda job : job['stage'] == 'unit-test' and job['status'] == 'success',jobs)))
                    if (nb_unit_tests_completed >= UNIT_TEST_JOBS_COUNT):
                        print("pipeline_state: UNIT_TESTS -> BUILD")
                        self.pipeline_state = 'BUILD'
                        self.raspberry.play_unit_tests_completed()
                elif (self.pipeline_state == 'BUILD'):
                    nb_build_completed = len(list(filter(lambda job : job['stage'] == 'build' and job['status'] == 'success',jobs)))
                    if (nb_build_completed >= BUILD_JOBS_COUNT):
                        print("pipeline_state: BUILD -> PACKAGE")
                        self.pipeline_state = 'PACKAGE'
                        self.raspberry.play_build_completed()
                elif (self.pipeline_state == 'PACKAGE'):
                    nb_build_completed = len(list(filter(lambda job : job['stage'] == 'docker-package' and job['status'] == 'success',jobs)))
                    if (nb_build_completed >= DOCKER_PACKAGE_JOBS_COUNT):
                        print("pipeline_state: BUILD -> DEPLOY")
                        self.pipeline_state = 'DEPLOY'
                        self.raspberry.play_package_completed()
                elif (self.pipeline_state == 'DEPLOY'):
                    nb_build_completed = len(list(filter(lambda job : job['stage'] == 'deploy-review' and job['status'] == 'success',jobs)))
                    if (nb_build_completed >= DEPLOY_JOBS_COUNT):
                        print("pipeline_state: DEPLOY -> FINISHED")
                        self.pipeline_state = 'FINISHED'
                        self.raspberry.play_deploy_completed()
            else:
                # We have a strange stage, let's exit
                self.raspberry.set_pin_state(False)
                self.global_state = 'WAITING'

    
    # retrieve 'last' pipeline from a list of pipelines
    def __get_last_pipeline(self):
        all_pipelines = self.get_pipelines()
        last_pipeline = reduce((lambda x, y: self.__select_most_recent_pipeline(x,y)), all_pipelines)
        return last_pipeline

    # retrieve 'last' pipeline from a set of two pipelines
    def __select_most_recent_pipeline(self, x, y):
        if (x['id'] > y['id']):
            return x
        else:
            return y    

    # retrieve all pipelines of current project (without pagination handling, list is sorted and we want only the last running pipeline)
    def get_pipelines(self):
        print('Retrieving last 5 pipelines')
        pipelines = requests.get(GET_PIPELINES + '?order_by=id&sort=desc&page=1&per_page=5', headers=HEADERS).json()
        for pipeline in pipelines:
            print('pipeline id={} status={}'.format(pipeline['id'],pipeline['status']))
        return pipelines

    # retrieve current pipeline
    def get_single_pipeline(self):
        pipeline_id = self.pipeline['id']
        print('Retrieving current pipeline id={}'.format(pipeline_id))
        pipeline = requests.get(GET_PIPELINES + '/' + str(pipeline_id), headers=HEADERS).json()
        print('pipeline id={} status={}'.format(pipeline['id'],pipeline['status']))
        return pipeline

    # retrieve jobs from current pipeline (with pagination handling)
    def get_jobs_from_pipeline(self):
        pipeline_id = self.pipeline['id']
        print('Retrieving current pipeline id={}'.format(pipeline_id))
        url = GET_PIPELINES + '/' + str(self.pipeline['id']) + '/jobs'
        jobs = []
        while (len(url) > 0):
            print('Retrieving ' + url)
            result = requests.get(url, headers=HEADERS)
            jobs.extend(result.json())
            url = self.extract_next_link_from_header(result.headers['Link'])
        for job in jobs:
            print('job id={} stage={} name={} status={}'.format(job['id'],job['stage'],job['name'],job['status']))
        return jobs

    def extract_next_link_from_header(self, linkData):
        items = linkData.split(",")
        for item in items:
            subitems = item.split(';')
            if (subitems[1].strip() == 'rel="next"'):
                return subitems[0].strip()[1:-1]
        return ''
        

