#!/usr/bin/env python2
#coding=utf-8

import sys
sys.path.insert(1,"modules") # All project specific modules go here
from modules import interface

extractorInterface = interface.Interface(__file__,"Extracts text from files in an Amazon S3 bucket")
extractorInterface.init()

extractorInterface.info("Starting extractor")
