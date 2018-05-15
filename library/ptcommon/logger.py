import logging
from systemd.journal import JournalHandler
from datetime import datetime


class LoggerSingleton:

    log_level_indicators = {10: 'D', 20: 'I', 30: 'W', 40: 'E', 50: '!'}

    def __init__(self, decorated):
        self._decorated = decorated
        self._added_handler = False
        self.setup_logging()

    def get_instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `get_instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

    def _print_message(self, message, level):
        if (self._log_to_journal is False and self._logging_level <= level):
            print("[" + datetime.now().strftime("%H:%M:%S.%f") + " " + self.log_level_indicators[level] + "] " + message)

    def setup_logging(self, logger_name="PTLogger", logging_level=20, log_to_journal=False):

        self._logging_level = logging_level
        self._log_to_journal = log_to_journal

        self._journal_log = logging.getLogger(logger_name)

        if (self._added_handler is False and log_to_journal is True):
            self._journal_log.addHandler(JournalHandler())
            self._added_handler = True

        self._journal_log.setLevel(self._logging_level)
        self._journal_log.info("Logger created.")

    def debug(self, message):
        self._print_message(message, logging.DEBUG)
        if (self._log_to_journal is True):
            self._journal_log.debug(message)

    def info(self, message):
        self._print_message(message, logging.INFO)
        if (self._log_to_journal is True):
            self._journal_log.info(message)

    def warning(self, message):
        self._print_message(message, logging.WARNING)
        if (self._log_to_journal is True):
            self._journal_log.warning(message)

    def error(self, message):
        self._print_message(message, logging.ERROR)
        if (self._log_to_journal is True):
            self._journal_log.error(message)


@LoggerSingleton
class PTLogger:

    def __init__(self):
        pass
