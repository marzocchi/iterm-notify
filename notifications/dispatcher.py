from typing import Callable, Optional
from logging import Logger


class Dispatcher:
    def __init__(self, logger: Optional[Logger] = None):
        self._logger = logger
        self._handlers: dict[str: Callable[[list], None]] = {}

    def register_handler(self, selector: str, handler: Callable):
        self._handlers[selector] = handler

    def dispatch(self, selector: str, args: list):
        if selector not in self._handlers:
            raise RuntimeError("can't dispatch to unknown selector: {}".format(selector))

        self._logger and self._logger.info("dispatching {} with args: {}".format(selector, args))
        try:
            self._handlers[selector](*args)
        except:
            self._logger and self._logger.exception("exception while dispatching {} with {}".format(selector, args))
