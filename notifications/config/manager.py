import json
import logging
import typing
from typing import Optional, List
from pathlib import Path

from notifications import config


class _Storage(typing.Protocol):
    def load(self) -> dict:
        pass

    def save(self, data: dict):
        pass


class FileStorage:
    def __init__(self, path: Path, logger: Optional[logging.Logger] = None):
        self._logger = logger
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
            txt = json.dumps(data)
            f.write(txt)


class Manager:
    def __init__(self, storage: _Storage, logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._storage = storage
        self._data = {}

    def load(self, existing_session_ids: List[str]):
        data = self._storage.load()
        valid_data = {}
        discarded = []

        for sid in existing_session_ids:
            if sid in data:
                valid_data[sid] = data[sid]
            else:
                discarded.append(sid)

        self._data = valid_data
        self._storage.save(self._data)

    def get(self, session_id) -> Optional[config.Stack]:
        return config.Stack.from_dict(self._data[session_id]) if session_id in self._data else None

    def delete(self, session_id):
        if session_id not in self._data:
            return

        del self._data[session_id]
        self._storage.save(self._data)

    def register(self, session_id: str, stack: config.Stack):
        self._data[session_id] = stack.to_dict()
        self._storage.save(self._data)

        def f():
            self._data[session_id] = stack.to_dict()
            self._storage.save(self._data)

        stack.on_pop += f
        stack.on_push += f
        stack.on_change += f
