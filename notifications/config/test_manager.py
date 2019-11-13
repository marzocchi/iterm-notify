from unittest import TestCase
from unittest.mock import MagicMock
from notifications.config import Manager
from copy import copy


class TestManager(TestCase):
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
                "command-complete-timeout": 0,
                "notifications-backend": "",
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
        mock_storage = MagicMock(['load', 'save'])
        mock_storage.load = MagicMock(return_value=self.SAMPLE_DATA)

        mgr = Manager(mock_storage)
        mgr.load(['CURRENT_SESSION'])

        self.assertEqual(self.SAMPLE_DATA['CURRENT_SESSION'], mgr.get('CURRENT_SESSION').to_dict())
        self.assertIsNone(mgr.get('DELETED_SESSION'))

        expected_saved_data = copy(self.SAMPLE_DATA)
        del expected_saved_data['DELETED_SESSION']

        mock_storage.save.assert_called_once_with(expected_saved_data)
