#coding=utf-8
import sys
sys.path.insert(1,"modules") # All project specific modules go here

import argparse, argcomplete
import logging

class Interface:
	"""This class represents the common user interface shared amongst ProtoKollen scripts
	   It handles common parameters, error message formatting, alerts, and the like.
	"""

	NORMAL_MODE   = 0
	DRY_MODE      = 1

	def __init__(self, description):
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

	def parse_args(self):
		argcomplete.autocomplete(self.parser)
		self.args = self.parser.parse_args()

		self.logLevel = self.args.loglevel * 10 #https://docs.python.org/2/library/logging.html#levels
		logging.basicConfig(
			level=self.logLevel,
			format='%(asctime)s %(levelname)s: %(message)s'
			)

		if self.args.dryrun:
			logging.info("Running in dry mode")
			self.executionMode = self.DRY_MODE
		else:
			logging.info("Running in normal mode")
			self.executionMode = self.NORMAL_MODE

		return self.args

	def dryMode(self):
		return bool(self.executionMode)
