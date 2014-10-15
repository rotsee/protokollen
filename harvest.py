#!/usr/bin/env python2
#coding=utf-8

import login
import settings
from modules.interface import Interface
commandLineArgs = [{
	"short" : "-s", "long" : "--super-dry",
	"dest"  : "superdryrun",
	"action": "store_true",
	"help"  : "Super dry. A dry run where we do not even download any files."
	},{
	"short" : "-t",	"long" : "--tolarated-changes",
	"type"	: int,
	"default":1,
	"dest"  : "tolaratedchanges",
	"metavar":"CHANGES",
	"help"  : "When should we warn about suspicios changes in the number of protocols? 1 means that anything other that zero or one new protocol since last time is considered suspicios."
	},{
	"short" : "-f",	"long" : "--file",
	"dest"  : "filename",
	"help"  : "Enter a file name, if your data source is a local CSV file. Otherwise, we will look for a Google Spreadsheets ID in login.py."
	}]
ui = Interface(__file__,
	"This script will download all files pointed out by a series of URLs and xPath expressions, and upload them to an Amazon S3 server.",
	commandLineArgs=commandLineArgs)

import datasheet #datasheet contains classes for storing data sets
if ui.args.filename is not None:
	ui.info("Harvesting from CSV file `%s`" % ui.args.filename)
	dataSet = datasheet.CSVFile(ui.args.filename)
elif login.google_spreadsheet_key is not None:
	ui.info("Harvesting from Google Spreadsheet`%s`" % login.google_spreadsheet_key)
	dataSet = datasheet.GoogleSheet(login.google_spreadsheet_key,login.google_client_email,login.google_p12_file)
else:
	ui.error("No local file given, and no Google Spreadsheet key found. Cannot proceed.")
	ui.exit()

suddenChangeThreshold = ui.args.tolaratedchanges

Interface.SUPERDRY_MODE = 2 #add an extra level of dryness
if ui.args.superdryrun:
	ui.info("Running in super dry mode")
	ui.executionMode = Interface.SUPERDRY_MODE

ui.info("Connecting to S3")
import upload
uploader = upload.S3Uploader(login.aws_access_key_id,login.aws_secret_access_key,login.aws_bucket_name)

ui.info("Setting up virtual browser")
import surfer
browser = surfer.Surfer()

import download
import hashlib
dataSet = dataSet.filter(require=["municipality","year","url","dlclick1"])
dataSet.shuffle() #give targets some rest between requests by scrambling the rows
ui.info("Data contains %d rows" % dataSet.getLength())
ui.debug(dataSet.data)

for row in dataSet.getNext():
	municipality = row["municipality"]
	year         = row["year"]
	url          = row["url"]
	preclick     = row.get("preclick1",None)
	dlclick1     = row["dlclick1"]
	dlclick2     = row.get("dlclick2",None)

	ui.info("Processing %s %s" % (municipality,year))
	browser.surfTo(url)

	if preclick is not None:
		ui.info("Preclicking")
		browser.clickOnStuff(preclick)

	ui.info("Getting URL list")
	urlList = browser.getUrlList(dlclick1)
	if len(urlList) == 0:
		ui.warning("No URLs found in %s %s" %  (municipality,year))

	#Sanity check. Do we have a resonable amount of URLs?
	alreadyUploadedListLength = uploader.getFileListLength(municipality + "/" + year)
	if alreadyUploadedListLength > 0 and ((abs(alreadyUploadedListLength - len(urlList)) > suddenChangeThreshold) or (len(urlList) < alreadyUploadedListLength) ):
		ui.warning("There was a sudden change in the number of download URLs for this municipality and year.")

	for downloadUrl in urlList:
		#TODO iterate over extra dlclicks
		if not downloadUrl.is_absolute():
			downloadUrl.makeAbsolute

		if dlclick2 is not None:
			ui.debug("Entering two step download")
			browser.surfTo(downloadUrl.href)
			urlList2 = browser.getUrlList(dlclick2)
			if len(urlList2) == 0:
				ui.warning("No match for second download xPath (%s)" % dlclick2)
				continue
			elif len(urlList2) > 1:
				ui.warning("Multiple matches on second download xPath (%s). Results might be unexpected." % dlclick2)
			downloadUrl = urlList2[0]
			if not downloadUrl.is_absolute():
				downloadUrl.makeAbsolute

		filename = hashlib.md5(downloadUrl.href).hexdigest()
		remoteNakedFilename = municipality + "/" + year + "/" + filename #full filename, but no suffix yet
		localNakedFilename = "temp/"+filename
		if uploader.fileExists(remoteNakedFilename):
			continue #File is already on Amazon

		if not downloadUrl.is_absolute():
			downloadUrl.makeAbsolute

		if ui.executionMode < Interface.SUPERDRY_MODE:
			downloadFile = download.FileFromWeb(downloadUrl.href,localNakedFilename)
			if downloadFile.success:
				filetype = downloadFile.getFileType()
				if filetype in settings.allowedFiletypes:
					remoteFullFilename = remoteNakedFilename + "." + filetype
					if ui.executionMode < Interface.DRY_MODE:
						uploader.putFile(localNakedFilename,remoteFullFilename)
				else:
					ui.warning("%s is not a valid mime type" % downloadFile.mimeType)
				downloadFile.delete()
			else:
				ui.warning("Download failed for %s" % downloadUrl)
browser.kill()