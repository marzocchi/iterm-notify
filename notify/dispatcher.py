from typing import Callable, Optional, Dict
from logging import Logger


class Dispatcher:
    def __init__(self, logger: Logger):
        self.__logger = logger
        self.__handlers: Dict[str, Callable[[list], None]] = {}

    def register_handler(self, selector: str, handler: Callable):
        self.__handlers[selector] = handler

    def dispatch(self, selector: str, args: list):
        if selector not in self.__handlers:
            raise RuntimeError("can't dispatch to unknown selector: {}".format(selector))

        self.__logger.info("dispatching {} with args: {}".format(selector, args))

        try:
            self.__handlers[selector](*args)
        except:
            self.__logger.exception("exception while dispatching {} with {}".format(selector, args))
