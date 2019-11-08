from unittest import TestCase
from unittest.mock import MagicMock
from notifications import preferences
from tempfile import NamedTemporaryFile
import json


class _Logger(object):
    def debug(self, msg: str): pass

    def info(self, msg: str): pass

    def warning(self, msg: str): pass

    def error(self, msg: str): pass

    def critical(self, msg: str): pass


class MockStorage(object):
    def load(self) -> dict:
        pass

    def save(self, data: dict):
        pass


class TestPreferences(TestCase):
    def test_get_by_session_id(self):
        storage = MockStorage()

        storage.load = MagicMock(return_value={'some_session': {'some_pref': 1}})

        prefs = preferences.Preferences(storage=storage, logger=_Logger())
        prefs.load()

        self.assertEqual({'some_pref': 1}, prefs.get('some_session'))
        self.assertEqual({}, prefs.get('some_other_session'))

        storage.load.assert_called_once()

    def test_prune(self):
        storage = MockStorage()

        storage.load = MagicMock(
            return_value={'some_session': {'some_pref': 1}, 'some_other_session': {'some_prefs': 2}})

        prefs = preferences.Preferences(storage=storage, logger=_Logger())
        prefs.load()

        prefs.prune(['some_other_session'])

        self.assertEqual({}, prefs.get('some_session'))
        self.assertEqual({'some_prefs': 2}, prefs.get('some_other_session'))

    def test_handler(self):
        storage = MockStorage()
        storage.load = MagicMock(return_value={})
        storage.save = MagicMock(return_value=None)

        prefs = preferences.Preferences(storage=storage, logger=_Logger())
        prefs.load()

        f = prefs.handler("some_session")

        f({'some_prefs': 1})

        storage.save.assert_called_once()

        storage.save.assert_called_with({'some_session': {'some_prefs': 1}})


class TestFileStorage(TestCase):
    def test_load_empty_file(self):
        f = NamedTemporaryFile()
        fs = preferences.FileStorage(path=f.name)

        stuff = fs.load()
        self.assertEqual({}, stuff)

    def test_load(self):
        with NamedTemporaryFile(mode='w') as f:
            f.write(json.dumps({'some_session': {'some_prefs': 1}}))

        fs = preferences.FileStorage(path=f.name)

        stuff = fs.load()
        self.assertEqual({}, stuff)

    def test_save(self):
        f = NamedTemporaryFile()

        fs = preferences.FileStorage(path=f.name)
        fs.save({'some_session': {'some_prefs': 1}})

        self.assertEqual({'some_session': {'some_prefs': 1}}, json.loads(f.read()))
