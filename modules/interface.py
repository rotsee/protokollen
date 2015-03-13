# -*- coding: utf-8 -*-
"""This module is included in the main entry points of ProtoKollen,
   to provide common functionality, such as error handling, etc.
"""

import sys
sys.path.insert(1, "modules")  # All project specific modules go here

import argparse
import argcomplete
import logging
from modules.errors import ErrorReport

FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT)


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Interface:
    """This class represents the common user interface shared amongst
       ProtoKollen scripts.
       It handles error message formatting, alerts, and the like.
    """

    NORMAL_MODE = 0
    DRY_MODE = 1

    def __init__(self, name, description, commandline_args=[]):
        """Command line arguments can also be put in a file named
           SCRIPTNAME_args.py, e.g. `harvest_args.py`.
        """
        self.parser = argparse.ArgumentParser(description)
        self.parser.add_argument(
            "-l", "--loglevel",
            dest="loglevel",
            help="""Log level.
                    5=only critical, 4=errors, 3=warnings, 2=info, 1=debug.
                    Setting this to 1 will print a lot! Default=3.)""",
            type=int,
            choices=(1, 2, 3, 4, 5),
            default=3)
        self.parser.add_argument(
            "-d", "--dry",
            dest="dryrun",
            action='store_true',
            help="Dry run. Do not upload files, or put stuff in databases.")

        # Check for FILENAME_args.py file
        import __main__
        import os
        try:
            filename = os.path.basename(__main__.__file__)
            filename = os.path.splitext(filename)[0]
            args_from_file = __import__(filename + "_args")
            commandline_args = commandline_args + args_from_file.args
        except ImportError:
            pass

        for c in commandline_args:
            self.parser.add_argument(
                c.pop("short", None),
                c.pop("long", None),
                **c)

        argcomplete.autocomplete(self.parser)
        self.args = self.parser.parse_args()

        self.logger = logging.getLogger(name)

        # https://docs.python.org/2/library/logging.html#levels
        self.logger.setLevel(self.args.loglevel * 10)

        self.executionMode = self.NORMAL_MODE
        if self.args.dryrun:
            self.logger.info("Running in dry mode")
            self.executionMode = self.DRY_MODE

    def post_error(self, level, msg):
        """Calls the error reporting API
        """
        error_report = ErrorReport(msg)
        error_report.level = level
        error_report.post()

    # Convenience shortcuts to logger methods
    def log(self, msg, mode=logging.INFO):
        self.logger.log(mode, msg)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = TerminalColors.WARNING + msg + TerminalColors.ENDC
        self.logger.warning(msg, *args, **kwargs)
        self.post_error(logging.WARNING, msg)

    def error(self, msg, *args, **kwargs):
        msg = TerminalColors.FAIL + msg + TerminalColors.ENDC
        self.logger.error(msg, *args, **kwargs)
        self.post_error(logging.ERROR, msg)

    def critical(self, msg, *args, **kwargs):
        msg = TerminalColors.FAIL + TerminalColors.BOLD + \
            msg + TerminalColors.ENDC
        self.logger.critical(msg, *args, **kwargs)
        self.post_error(logging.CRITICAL, msg)

    def dry_mode(self):
        return bool(self.executionMode)

    def ask_if_continue(self, default="no", message="Really continue?"):
        """Ask a yes/no question via raw_input() and return their answer

           Command line implementation from
           http://code.activestate.com/recipes/577058/
        """
        valid = {"yes": True, "y": True, "ja": True,
                 "no": False, "n": False, "nej": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while 1:
            sys.stdout.write(message + prompt)
            choice = raw_input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid.keys():
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")

    def exit(self):
        import sys
        sys.exit()

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
