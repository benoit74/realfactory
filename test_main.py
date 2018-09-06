from gitlab import Gitlab
from unittest.mock import MagicMock
from raspberry import Raspberry
import unittest
import json 
import os

class TestGitlab(unittest.TestCase):

    def test_init(self):
        g = Gitlab(None)
        self.assertEqual(g.global_state, 'NOT_INITIALIZED')

    def test_update_not_initialized(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        g = Gitlab(r)
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_called_once_with(False)

    def setup_get_pipelines_reply(self, g, status1, status2):
        test_pipelines_str = """[
            {{
                "id": 47,
                "status": "{}",
                "ref": "new-pipeline",
                "sha": "a91957a858320c0e17f3a0eca7cfacbff50ea29a"
            }},
            {{
                "id": 48,
                "status": "{}",
                "ref": "new-pipeline",
                "sha": "eb94b618fb5865b26e80fdd8ae531b7a63ad851a"
            }}
        ]""".format(status1, status2)
        test_pipelines = json.loads(test_pipelines_str)
        g.get_pipelines = MagicMock(return_value=test_pipelines) 

    def setup_get_single_pipeline_reply(self, g, status):
        test_pipeline_str = """
            {{
                "id": 48,
                "status": "{}",
                "ref": "new-pipeline",
                "sha": "eb94b618fb5865b26e80fdd8ae531b7a63ad851a"
            }}
        """.format(status)
        test_pipeline = json.loads(test_pipeline_str)
        g.get_single_pipeline = MagicMock(return_value=test_pipeline)
        
    def setup_get_pipeline_jobs_reply(self, g, status1, status2, status3, status4, status5, status6, status7, status8):
        test_pipeline_jobs_str = """
        [
            {{
                "id": 72,
                "stage": "unit-test",
                "status": "{}"
            }},
            {{
                "id": 73,
                "stage": "unit-test",
                "status": "{}"
            }},
            {{
                "id": 74,
                "stage": "unit-test",
                "status": "{}"
            }},
            {{
                "id": 75,
                "stage": "build",
                "status": "{}"
            }},
            {{
                "id": 76,
                "stage": "docker-package",
                "status": "{}"
            }},
            {{
                "id": 77,
                "stage": "docker-package",
                "status": "{}"
            }},
            {{
                "id": 78,
                "stage": "docker-package",
                "status": "{}"
            }},
            {{
                "id": 79,
                "stage": "deploy-review",
                "status": "{}"
            }}
        ]
        """.format(status1, status2, status3, status4, status5, status6, status7, status8)
        test_pipeline_jobs = json.loads(test_pipeline_jobs_str)
        g.get_jobs_from_pipeline = MagicMock(return_value=test_pipeline_jobs)

    def test_no_running_pipeline(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_pipeline_start = MagicMock()
        g = Gitlab(r)
        g.global_state = 'WAITING'
        self.setup_get_pipelines_reply(g, 'pending', 'pending')
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_not_called()
        r.play_pipeline_start.assert_not_called()

    def test_old_running_pipeline(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_pipeline_start = MagicMock()
        g = Gitlab(r)
        g.global_state = 'WAITING'
        self.setup_get_pipelines_reply(g, 'running', 'pending')
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_not_called()
        r.play_pipeline_start.assert_not_called()

    def test_last_running_pipeline(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'WAITING'
        g.pipeline_state = 'WHATEVER'
        self.setup_get_pipelines_reply(g, 'completed', 'running')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'UNIT_TESTS')
        r.set_pin_state.assert_called_once_with(True)
        r.play_sound.assert_called_once_with('pipeline_start')

    def test_running_pipeline_still_running(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'UNIT_TESTS'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'running', 'running', 'running', 'created', 'created', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'UNIT_TESTS')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_not_called()

    def test_running_pipeline_completed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        self.setup_get_single_pipeline_reply(g, 'success')
        self.setup_get_pipeline_jobs_reply(g, 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value')
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_called_once_with(False)
        r.play_sound.assert_called_once_with('pipeline_completed')

    def test_running_pipeline_failed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        self.setup_get_single_pipeline_reply(g, 'failed')
        self.setup_get_pipeline_jobs_reply(g, 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value', 'any_value')
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_called_once_with(False)
        r.play_sound.assert_called_once_with('pipeline_failed')

    def test_running_pipeline_still_running_unit_test_partially_completed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'UNIT_TESTS'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'running', 'running', 'created', 'created', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'UNIT_TESTS')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_not_called()

    def test_running_pipeline_still_running_unit_test_all_completed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'UNIT_TESTS'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'running', 'created', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'BUILD')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('unit_tests_completed')

    def test_running_pipeline_still_running_unit_test_and_build_completed_all(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'UNIT_TESTS'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'created', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'BUILD')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('unit_tests_completed')

    def test_running_pipeline_still_running_build_completed_all(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'BUILD'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'created', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'PACKAGE')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('build_completed')

    def test_running_pipeline_still_running_build_completed_with_deploy_as_well(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'BUILD'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'success', 'success', 'success', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'PACKAGE')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('build_completed')

    def test_running_pipeline_still_running_package_still_running(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'PACKAGE'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'success', 'created', 'created', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'PACKAGE')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_not_called()

    def test_running_pipeline_still_running_package_completed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'PACKAGE'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'success', 'success', 'success', 'created')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'DEPLOY')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('package_completed')

    def test_running_pipeline_still_running_deploy_completed(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'DEPLOY'
        self.setup_get_single_pipeline_reply(g, 'running')
        self.setup_get_pipeline_jobs_reply(g, 'success', 'success', 'success', 'success', 'success', 'success', 'success', 'success')
        g.update_state()
        self.assertEqual(g.global_state, 'RUNNING')
        self.assertEqual(g.pipeline_state, 'FINISHED')
        r.set_pin_state.assert_not_called()
        r.play_sound.assert_called_once_with('deploy_completed')

    def test_running_pipeline_abnormal_status(self):
        r = Raspberry(False)
        r.set_pin_state = MagicMock()
        r.play_sound = MagicMock()
        g = Gitlab(r)
        g.global_state = 'RUNNING'
        g.pipeline_state = 'WHATEVER'
        self.setup_get_single_pipeline_reply(g, 'abnormalvalue')
        self.setup_get_pipeline_jobs_reply(g, 'whatever', 'whatever', 'whatever', 'whatever', 'whatever', 'whatever', 'whatever', 'whatever')
        g.update_state()
        self.assertEqual(g.global_state, 'WAITING')
        r.set_pin_state.assert_called_once_with(False)
        r.play_sound.assert_not_called()

    def test_extract_next_link_from_header(self):
        r = Raspberry(False)
        g = Gitlab(r)
        res = g.extract_next_link_from_header('<https://gitlab.example.com/api/v4/projects/8/issues/8/notes?page=1&per_page=3>; rel="prev", <https://gitlab.example.com/api/v4/projects/8/issues/8/notes?page=3&per_page=3>; rel="next", <https://gitlab.example.com/api/v4/projects/8/issues/8/notes?page=1&per_page=3>; rel="first", <https://gitlab.example.com/api/v4/projects/8/issues/8/notes?page=3&per_page=3>; rel="last"')
        self.assertEqual(res, 'https://gitlab.example.com/api/v4/projects/8/issues/8/notes?page=3&per_page=3')
        
    


if __name__ == '__main__':
    unittest.main()