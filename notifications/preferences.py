import typing
import json
import logging
from pathlib import Path


class Storage(typing.Protocol):
    def load(self) -> dict:
        pass

    def save(self, data: dict):
        pass


class FileStorage:
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> dict:
        try:
            with open(str(self._path), 'r') as f:
                data = f.read().strip()
                if data == "":
                    return {}
                return json.loads(data)
        except FileNotFoundError:
            return {}

    def save(self, data: dict):
        with open(str(self._path), 'w') as f:
            f.write(json.dumps(data))


class Preferences:
    def __init__(self, storage: Storage, logger: logging.Logger):
        self._logger = logger
        self._storage = storage
        self._data = {}

    def get(self, session_id: str) -> dict:
        if session_id in self._data:
            return self._data[session_id]

        return {}

    def _save(self):
        self._storage.save(self._data)

    def prune(self, current_session_ids: list):
        new_data = {}
        discarded = []
        for sid in current_session_ids:
            if sid in self._data:
                new_data[sid] = self._data[sid]
            else:
                discarded.append(sid)

        self._logger.debug("discarded sessions: {}".format([k for k in discarded]))

        self._data = new_data
        self._save()

    def load(self):
        self._data = self._storage.load()

    def handler(self, session_id: str) -> typing.Callable[[dict], None]:
        def f(data: dict) -> None:
            self._data[session_id] = data
            self._save()

        return f
