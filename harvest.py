#!/usr/bin/env python2
#coding=utf-8

import sys
sys.path.insert(1,"modules") # All project specific modules go here

import login # Passwords and keys goes in login.py
import settings

import argparse, argcomplete
parser = argparse.ArgumentParser(
	description='This script will download all files pointed out by a series of URLs and xPath expressions, and upload them to an Amazon S3 server.')
parser.add_argument(
	"-l", "--loglevel",
	dest="loglevel",
    help="Log level. 5=only critical, 4=errors, 3=warnings, 2=info, 1=debug. Setting this to 1 will print a lot! Default=3.)",
    type=int,
    choices=(1,2,3,4,5),
    default=3 )

parser.add_argument(
	"-d", "--dry",
	dest="dryrun",
	action='store_true',
    help="Dry run. Do not upload any files to Amazon (only download and delete them).")

parser.add_argument(
	"-s", "--super-dry",
	dest="superdryrun",
	action='store_true',
	help="Super dry. A dry run where we do not even download any files.")

parser.add_argument(
	"-t", "--tolarated-changes",
	dest="tolaratedchanges",
	type=int,
	default=1,
	metavar="CHANGES",
	help="When should we warn about suspicios changes in the number of protocols? 1 means that anything other that zero or one new protocol since last time is considered suspicios.")

parser.add_argument(
	"-f", 	"--file",
	dest="filename",
	help="Enter a file name, if your data source is a local CSV file. Otherwise, we will look for a Google Spreadsheets ID in login.py")

argcomplete.autocomplete(parser)
args = parser.parse_args()

import logging
logLevel = args.loglevel * 10 #https://docs.python.org/2/library/logging.html#levels
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s %(levelname)s: %(message)s'
	)

import datasheet #datasheet contains classes for storing data sets
if args.filename is not None:
	logging.info("Harvesting from CSV file `%s`" % args.filename)
	dataSet = datasheet.CSVFile(args.filename)
elif login.google_spreadsheet_key is not None:
	logging.info("Harvesting from Google Spreadsheet`%s`" % login.google_spreadsheet_key)
	dataSet = datasheet.GoogleSheet(login.google_spreadsheet_key,login.google_client_email,login.google_p12_file)
else:
	logging.error("No local file given, and no Google Spreadsheet key found. Cannot proceed.")
	import sys
	sys.exit()

suddenChangeThreshold = args.tolaratedchanges

NORMAL_MODE   = 0
DRY_MODE      = 1
SUPERDRY_MODE = 2

if args.superdryrun:
	logging.info("Running in super dry mode")
	executionMode = SUPERDRY_MODE
elif args.dryrun:
	logging.info("Running in dry mode")
	executionMode = DRY_MODE
else:
	logging.info("Running in normal mode")
	executionMode = NORMAL_MODE

logging.info("Connecting to S3")
import upload
s3 = upload.S3Connection(login.aws_access_key_id,login.aws_secret_access_key,login.aws_bucket_name)

logging.info("Setting up virtual browser")
import surfer
browser = surfer.Surfer()

import download
import hashlib
dataSet = dataSet.filter(require=["municipality","year","url","dlclick1"])
dataSet.shuffle() #give targets some rest between requests by scrambling the rows
for row in dataSet.getNext():
	municipality = row["municipality"]
	year         = row["year"]
	url          = row["url"]
	preclick     = row["preclick1"]
	dlclick1     = row["dlclick1"]
	dlclick2     = row["dlclick2"]

	logging.info("Processing %s %s" % (municipality,year))

	browser.surfTo(url)

	if preclick is not None:
		logging.info("Preclicking")
		browser.clickOnStuff(preclick)

	logging.info("Getting URL list")
	urlList = browser.getUrlList(dlclick1)

	if len(urlList) == 0:
		logging.warning("No URLs found in %s %s" %  (municipality,year))

	#Sanity check. Do we have a resonable amount of URLs?
	alreadyUploadedListLength = s3.getBucketListLength(municipality + "/" + year)
	if alreadyUploadedListLength > 0 and ((abs(alreadyUploadedListLength - len(urlList)) > suddenChangeThreshold) or (len(urlList) < alreadyUploadedListLength) ):
		logging.warning("There was a sudden change in the number of download URLs for this municipality and year.")

	for downloadUrl in urlList:

		#TODO iterate over extra dlclicks
		if not downloadUrl.is_absolute():
			downloadUrl.makeAbsolute

		if dlclick2 is not None:
			logging.debug("Entering two step download")
			browser.surfTo(downloadUrl.href)
			urlList2 = browser.getUrlList(dlclick2)
			if len(urlList2) == 0:
				logging.warning("No match for second download xPath (%s)" % dlclick2)
				continue
			elif len(urlList2) > 1:
				logging.warning("Multiple matches on second download xPath (%s). Results might be unexpected." % dlclick2)
			downloadUrl = urlList2[0]
			if not downloadUrl.is_absolute():
				downloadUrl.makeAbsolute

		filename = hashlib.md5(downloadUrl.href).hexdigest()
		remoteNakedFilename = municipality + "/" + year + "/" + filename #full filename, but no suffix yet
		localNakedFilename = "temp/"+filename
		if s3.fileExistsInBucket(remoteNakedFilename):
			continue #File is already on Amazon

		if not downloadUrl.is_absolute():
			downloadUrl.makeAbsolute

		if executionMode < SUPERDRY_MODE:
			downloadFile = download.File(downloadUrl.href,localNakedFilename)
			if downloadFile.success:
				filetype = downloadFile.getFileType()

				if filetype in settings.allowedFiletypes:
					remoteFullFilename = remoteNakedFilename + "." + filetype
					if executionMode < DRY_MODE:
						s3.putFile(localNakedFilename,remoteFullFilename)
				else:
					logging.warning("%s is not a valid mime type" % downloadFile.mimeType)

				downloadFile.delete()
			else:
				logging.warning("Download failed for %s" % downloadUrl)

browser.kill()