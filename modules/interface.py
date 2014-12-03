#coding=utf-8
"""This module is included in the main entry points of ProtoKollen,
   to provide common functionality, such as error handling, etc.
"""

import sys
sys.path.insert(1, "modules")  # All project specific modules go here

import argparse
import argcomplete
import logging
FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT)


class Interface:
    """This class represents the common user interface shared amongst
       ProtoKollen scripts.
       It handles error message formatting, alerts, and the like.
    """

    NORMAL_MODE = 0
    DRY_MODE = 1

    def __init__(self, name, description, commandLineArgs=[]):
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
            help="Dry run. Do not upload any files, or put stuff in databases.")

        # Check for FILENAME_args.py file
        import __main__
        import os
        try:
            filename = os.path.basename(__main__.__file__)
            filename = os.path.splitext(filename)[0]
            args_from_file = __import__(filename + "_args")
            commandLineArgs = commandLineArgs + args_from_file.args
        except ImportError:
            pass

        for c in commandLineArgs:
            self.parser.add_argument(
                c.pop("short", None),
                c.pop("long", None),
                **c)

        argcomplete.autocomplete(self.parser)
        self.args = self.parser.parse_args()

        self.logger = logging.getLogger(name)
        # Use handler, to print to stdout, not stderr
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.args.loglevel * 10)  # https://docs.python.org/2/library/logging.html#levels
        self.logger.addHandler(ch)
#        self.logger.setLevel(self.args.loglevel * 10)  # https://docs.python.org/2/library/logging.html#levels

        self.executionMode = self.NORMAL_MODE
        if self.args.dryrun:
            self.logger.info("Running in dry mode")
            self.executionMode = self.DRY_MODE

    #Convenience shortcuts to logger methods
    def log(self, msg, mode=logging.INFO):
        self.logger.log(mode, msg)
    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)
    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)
    def warning(self, *args, **kwargs):
        self.logger.warning(*args, **kwargs)
    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)
    def critical(self, *args, **kwargs):
        self.logger.critical(*args, **kwargs)

    def dryMode(self):
        return bool(self.executionMode)

    def exit(self):
        import sys
        sys.exit()
