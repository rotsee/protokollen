#coding=utf-8
"""This module is included in the main entry points of ProtoKollen, to provide common functionality,
   such as error handling, etc. 
"""

import sys
sys.path.insert(1,"modules") # All project specific modules go here

import argparse, argcomplete
import logging
FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT)

class Interface:
	"""This class represents the common user interface shared amongst ProtoKollen scripts
	   It handles common parameters, error message formatting, alerts, and the like
	"""

	NORMAL_MODE   = 0
	DRY_MODE      = 1

	def __init__(self, name, description):
		self.parser = argparse.ArgumentParser(description)
		self.parser.add_argument(
			"-l", "--loglevel",
			dest="loglevel",
		    help="Log level. 5=only critical, 4=errors, 3=warnings, 2=info, 1=debug. Setting this to 1 will print a lot! Default=3.)",
		    type=int,
		    choices=(1,2,3,4,5),
		    default=3 )
		self.parser.add_argument(
			"-d", "--dry",
			dest="dryrun",
			action='store_true',
		    help="Dry run. Do not upload any files, or put stuff in databases.")

		self.executionMode = self.NORMAL_MODE
		self.args = {}
		self.isInitiated = False
		self.logger = logging.getLogger(name)

	def init(self):
		argcomplete.autocomplete(self.parser)
		self.args = self.parser.parse_args()

		self.logger.setLevel(self.args.loglevel * 10) #https://docs.python.org/2/library/logging.html#levels

		if self.args.dryrun:
			self.logger.info("Running in dry mode")
			self.executionMode = self.DRY_MODE

		self.isInitiated = True

	def log(self,msg,mode=logging.INFO):
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
		if not self.isInitiated:
			self.logger.warning("Interface:dryMode() was called before Interface:init()")
		return bool(self.executionMode)
