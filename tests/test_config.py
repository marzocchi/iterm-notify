import logging
from copy import copy
from unittest.case import TestCase
from unittest.mock import Mock

from notify.config import SessionManager, Stack, create_default


class TestSessionManager(TestCase):
    SAMPLE_DATA = {
        "CURRENT_SESSION": [
            {
                "success-title": "success!",
                "success-message": "",
                "success-icon": None,
                "success-sound": None,
                "failure-title": "",
                "failure-message": "",
                "failure-icon": None,
                "failure-sound": None,
                "notifications-strategy": {"name": "test", "args": []},
                "notifications-backend": {"name": "test", "args": []},
                "logger-name": "",
                "logger-level": ""
            }
        ],
        "DELETED_SESSION": [
            {
                "success-title": "success!",
            }
        ]
    }

    def test_load_prunes_dead_sessions(self):
        mock_storage = Mock(['load', 'save'])
        mock_storage.load = Mock(return_value=self.SAMPLE_DATA)

        mgr = SessionManager(mock_storage, logger=Mock(spec=logging.Logger))
        mgr.load_and_prune(['CURRENT_SESSION'])

        expected_saved_data = copy(self.SAMPLE_DATA)
        del expected_saved_data['DELETED_SESSION']

        mock_storage.save.assert_called_once_with(expected_saved_data)


class TestStack(TestCase):
    def test_push_pop(self):
        cfg = create_default("foo")

        s = Stack([cfg])

        self.assertEqual("foo", s.current.logger_name)

        s.push()
        self.assertEqual("foo", s.current.logger_name)

        s.logger_name = "bar"
        self.assertEqual("bar", s.current.logger_name)

        old = s.pop()
        self.assertEqual("bar", old.logger_name)
        self.assertEqual("foo", s.current.logger_name)

        with self.assertRaises(IndexError):
            s.pop()

    def test_on_pop(self):
        cfg = create_default("foo")

        s = Stack([cfg])

        s.logger_name = "foo"
        s.push()

        s.logger_name = "bar"
        f = Mock()

        s.on_pop += f

        s.pop()
        f.assert_called_once()
