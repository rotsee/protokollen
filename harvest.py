#coding=utf-8

#TODO:
#Do not start virtual browser until we need it
#sendmail support
#multistep download is broken (test case: Bollnäs 2014).


import login # Passwords and keys goes in login.py

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

import datasheet
if args.filename is not None:
	logging.info("Harvesting from CSV file `%s`" % dataFile)
	dataSet = datasheet.CSVFile(dataFile)
elif login.google_spreadsheet_key is not None:
	logging.info("Harvesting from Google Spreadsheet`%s`" % login.google_spreadsheet_key)
	dataSet = datasheet.GoogleSheet(
		login.google_spreadsheet_key,
		login.google_client_email,
		login.google_p12_file)
else:
	logging.error("No local file given, and no Google Spreadsheet ID found in login.py. Cannot proceed.")
	import sys
	sys.exit()
dataSet.shuffle() #give targets some rest between requests by scrambling the rows

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

########## SETTINGS ######################################
                                                         #
#dataFile = "Kommunstyrelseprotokoll (tidigare Dokument i Dalarna) - Sheet1.csv"                                    #
allowedFiletypes = ['pdf','doc','docx']                  #
                                                         #
##########################################################

import urlparse
def is_absolute(url):
	"""Check if url is absolute or relative"""
	return bool(urlparse.urlparse(url).netloc)

##########################################################

logging.info("Connecting to S3")
import upload
s3 = upload.S3Connection(
	login.aws_access_key_id,
	login.aws_secret_access_key,
	login.aws_bucket_name)

logging.info("Setting up virtual browser")
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from xvfbwrapper import Xvfb
vdisplay = Xvfb()
vdisplay.start()
# We need a separate browser for the second download click
profile = webdriver.FirefoxProfile()
profile2 = webdriver.FirefoxProfile()
#profile.set_preference("browser.link.open_newwindow", 1)
browser = webdriver.Firefox(profile)
browser2 = webdriver.Firefox(profile2)

import download
import hashlib

for row in dataSet.getNext():
	municipality = row["municipality"]
	year         = row["year"]
	url          = row["url"]
	preclick     = row["preclick1"]
	dlclick1     = row["dlclick1"]
	dlclick2     = row["dlclick2"]

	if dlclick1 is None or municipality is None or year is None or url is None:

		logging.warning("A required field is missing from %s (%s). We will skip this row." % (municipality,year))
	else:

		logging.info("Processing %s %s" % (municipality,year))

		#Make sure whatever element we are looking for is loaded before continuing
		if preclick is not None:
			pageLoadedCheck = preclick
		else:
			pageLoadedCheck = dlclick1
		browser.get(url)
		#Until we make WebDriverWait work, just wait 3 extra seconds, that seems to be enough
		browser.implicitly_wait(3)
# FIXME 
#					try:
#					    elements = WebDriverWait(browser, 10).until(
#					    	ExpectedConditions.visibilityOfElementLocated(
#					    		By.xpath(pageLoadedCheck)))
#					    print elements
#					except:
#						logging.warning("Page at %s timed out, or first xPath (%s) wasn't found" % (url,pageLoadedCheck))
#						browser.quit()

		if preclick is not None:
			logging.info(" Preclicking")
			elementList = browser.find_elements_by_xpath(preclick)
			if not elementList:
				logging.warning("  Preclick required but no elements found for xPath %s" % preclick)
			for element in elementList:
				element.click()
			browser.implicitly_wait(8)

		logging.info(" Getting URL list")
		urllistSelenium = browser.find_elements_by_xpath(dlclick1)
		if len(urllistSelenium) == 0:
			logging.warning("  No URLs found")
		else:
			#Sanity check. Do we have a resonable amount of URLs?
			alreadyUploadedListLength = s3.getBucketListLength(municipality + "/" + year)
			if alreadyUploadedListLength > 0 and ((abs(alreadyUploadedListLength - len(urllistSelenium)) > suddenChangeThreshold) or (len(urllistSelenium) < alreadyUploadedListLength) ):
				logging.warning("  There was a sudden change in the number of download URLs for this municipality and year.")

			for u in urllistSelenium:
				downloadUrl = u.get_attribute("href")
				if not downloadUrl:
					pass #Silently ignore false positives in xPath
				else:
					if dlclick2 is not None:
						logging.info("  Entering two step download")
						browser2.get(downloadUrl)
						browser2.implicitly_wait(3)
						uList = browser2.find_elements_by_xpath(dlclick2)
						if len(uList) == 0:
							logging.warning("   No match for second download xPath (%s)" % dlclick2)
						elif len(uList) > 1:
							logging.warning("   Multiple matches on second download xPath (%s). Results might be unexpected." % dlclick2)
							for uu in uList:
								u = uu.get_attribute("href")
								if u:
									downloadUrl = u
						else:
							downloadUrl = uList[0].get_attribute("href")
						if not downloadUrl:
							logging.warning("   Two step download failed")

				if downloadUrl is not None:
					filename = hashlib.md5(municipality + "/" + year + "/" + filename).hexdigest()
					if s3.fileExistsInBucket(municipality + "/" + year + "/" + filename):
						pass #File is already on Amazon
					else:
						print("downloading")
						localFilename = "temp/"+filename

						if is_absolute(downloadUrl):
							pass #URL needs no modification
						else:
							#URL is relative, append base
							from urllib.parse import urlparse
							parse_object = urlparse(url)
							urlBase = parse_object.scheme + "://" + parse_object.netloc
							downloadUrl = urlBase + downloadUrl

						if executionMode < SUPERDRY_MODE:
							downloadFile = download.File(downloadUrl,localFilename)
							if downloadFile.success:
								filetype = downloadFile.getFileType()

								if filetype in allowedFiletypes:
									s3name = municipality + "/" + year + "/" + filename + "." + filetype
									if executionMode < DRY_MODE:
										s3.putFile(localFilename,s3name)
								else:
									logging.warning("%s is not a valid mime type" % downloadFile.mimeType)

								downloadFile.delete()

browser.close()
vdisplay.stop()