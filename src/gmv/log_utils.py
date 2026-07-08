'''
    Gmvault: a tool to backup and restore your gmail account.
    Copyright (C) <since 2011>  <guillaume Aubert (guillaume dot aubert at gmail do com)>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
import sys
import os

from loguru import logger as _loguru_logger

# remove the default loguru handler so that, by default, nothing is logged
# (mimics the previous NullHandler behaviour until a handler is setup)
_loguru_logger.remove()

#different types of LoggerFactory
STANDALONE = "STANDALONE"

#default log file
DEFAULT_LOG = "%s/gmvault.log" % (os.getenv("HOME", "."))


class LoguruLoggerFactory(object):
    """
       Factory for creating the right loguru handler
    """

    def __init__(self):
        pass

    def setup_cli_app_handler(self, activate_log_file=False, console_level='CRITICAL',
                              file_path=DEFAULT_LOG, log_file_level='DEBUG'):
        """
           Setup a handler for communicating with the user and still log everything in a logfile
        """
        _loguru_logger.remove()

        _loguru_logger.add(sys.stdout, level=console_level.upper(),
                           format="{message}")

        if activate_log_file:
            _loguru_logger.add(file_path, level=log_file_level.upper(), mode='w',
                               format="[{time:%Y-%m-%d %H:%M}]:{level}:{message}")

    def setup_simple_file_handler(self, file_path):
        """
           Push a file handler logging only the message (no timestamp)
        """
        _loguru_logger.remove()
        _loguru_logger.add(file_path, level="DEBUG", format="{message}")

    def setup_simple_stdout_handler(self):
        """
           Push a stdout handler logging only the message (no timestamp)
        """
        _loguru_logger.remove()
        _loguru_logger.add(sys.stdout, level="DEBUG", format="{message}")

    def setup_simple_stderr_handler(self):
        """
           Push a stderr handler logging only the message (no timestamp)
        """
        _loguru_logger.remove()
        _loguru_logger.add(sys.stderr, level="DEBUG", format="{message}")

    def get_logger(self, name):
        """
           Return a loguru logger
        """
        return _loguru_logger


class LoggerFactory(object):
    '''
       My Logger Factory
    '''
    _factory = LoguruLoggerFactory()
    _created = False

    @classmethod
    def get_factory(cls, the_type):
        """
           Get logger factory
        """

        if cls._created:
            return cls._factory

        if the_type == STANDALONE:
            cls._factory = LoguruLoggerFactory()
            cls._created = True
        else:
            raise Exception("LoggerFactory type %s is unknown." % (the_type))

        return cls._factory

    @classmethod
    def get_logger(cls, name):
        """
          Simply return a logger
        """
        return cls._factory.get_logger(name)


    @classmethod
    def setup_simple_stderr_handler(cls, the_type):
        """
           Push a stderr handler logging only the message (no timestamp)
        """
        cls.get_factory(the_type).setup_simple_stderr_handler()

    @classmethod
    def setup_simple_stdout_handler(cls, the_type):
        """
           Push a stderr handler logging only the message (no timestamp)
        """
        cls.get_factory(the_type).setup_simple_stdout_handler()

    @classmethod
    def setup_simple_file_handler(cls, the_type, file_path):
        """
           Push a file handler logging only the message (no timestamp)
        """
        cls.get_factory(the_type).setup_simple_file_handler(file_path)

    @classmethod
    def setup_cli_app_handler(cls, the_type, activate_log_file=False,
                              console_level='CRITICAL', file_path=DEFAULT_LOG,
                               log_file_level='DEBUG'):
        """
           init logging engine
        """
        cls.get_factory(the_type).setup_cli_app_handler(activate_log_file,
                                                        console_level,
                                                        file_path, log_file_level)
