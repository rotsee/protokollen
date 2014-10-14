#!/usr/bin/env python2
#coding=utf-8

import sys
sys.path.insert(1,"modules") # All project specific modules go here
from modules import interface

extractorInterface = interface.Interface("Extracts text from files in an Amazon S3 bucket")
args = extractorInterface.parse_args()

print extractorInterface.logLevel
