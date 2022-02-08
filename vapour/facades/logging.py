import logging


class LoggingMixin(object):

    @property
    def log(self):
        return logging.getLogger(self.__class__.__qualname__)