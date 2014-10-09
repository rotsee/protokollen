#coding=utf-8

import logging
########## SETTINGS ######################################
                                                         #
dataFile = "Kommunstyrelseprotokoll (tidigare Dokument i Dalarna) - Sheet1.csv"                                    #
logLevel = logging.INFO # DEBUG > INFO > WARNING > ERROR #
protokollenUserAgent = 'Protokollen; ProtoCollection (http://protokollen.net/)'
                                                         #
##########################################################

logging.basicConfig(
	level=logLevel,
	format='%(asctime)s %(message)s'
	)

import urlparse
def is_absolute(url):
	"""Check if url is absolute or relative"""
	return bool(urlparse.urlparse(url).netloc)

import urllib2
def dlfile(url,localpath):
	# TODO: Set User-agent to show who we are!
	try:
		url = url.encode('utf-8')
		req = urllib2.Request(url)
		req.add_header('User-agent', protokollenUserAgent)
		f = urllib2.urlopen(req)

		with open(localpath, "wb") as local_file:
			local_file.write(f.read())

	except urllib2.HTTPError, e:
		logging.warning("HTTP Error: %s %s" % (e.code, url) )
	except urllib2.URLError, e:
		logging.warning("URL Error: %s %s" % (e.reason, url) )

def getBucketListLength(pathFragment,bucket):
	l = bucket.list(pathFragment)
	i = 0
	for key in l:
		i += 1
	return i

def fileExistsInBucket(fullfilename,bucket):
	if getBucketListLength(fullfilename,bucket):
		return True
	else:
		return False

###########################################################################

logging.info("Starting a full harvesting loop on `%s`" % dataFile)

logging.info("Connecting to S3")
import login
from boto.s3.connection import S3Connection
conn = S3Connection(login.aws_access_key_id, login.aws_secret_access_key)
bucket = conn.get_bucket(login.aws_bucket_name)
from boto.s3.key import Key

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

logging.info("Fetching data from CSV file")
import datasheet
csvFile = datasheet.CSVFile(dataFile)
dataSet = datasheet.DataSet(csvFile.data)

import os
import hashlib
import magic
magicmime = magic.Magic(mime=True)

for row in dataSet.getNext():
	municipality = row["municipality"]
	year         = row["year"]
	url          = row["url"]
	preclick     = row["preclick1"]
	dlclick1     = row["dlclick1"]
	dlclick2     = row["dlclick2"]

	if dlclick1 == "" or municipality == "" or year == "" or url == "":

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
			alreadyUploadedListLength = getBucketListLength(municipality + "/" + year,bucket)
			if abs(alreadyUploadedListLength - len(urllistSelenium)) > 1:
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
					filename = hashlib.md5(url).hexdigest()
					if fileExistsInBucket(municipality + "/" + year + "/" + filename,bucket):
						pass #File is already on Amazon
					else:
						localFilename = "temp/"+filename

						if is_absolute(downloadUrl):
							pass #URL needs no modification
						else:
							#URL is relative, append base
							from urllib.parse import urlparse
							parse_object = urlparse(downloadUrl)
							urlBase = parse_object.scheme + "://" + parse_object.netloc
							downloadUrl = urlBase + downloadUrl

						dlfile(url,localFilename)

						if not os.path.isfile(localFilename):
							logging.warning("Failed to download file from %s" % downloadUrl)
						else:
							#Only accept some file types
							mimetype = magicmime.from_file(localFilename)
							if mimetype == 'application/pdf':
								filetype = 'pdf'
							elif mimetype == 'application/msword':
								filetype = 'doc'
							elif mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
								filetype = 'docx'
							else:
								filetype = None

							if filetype:
								k = Key(bucket)
								k.key = municipality + "/" + year + "/" + filename + "." + filetype
								k.set_contents_from_filename(localFilename)
							else:
								loggin.warning("Not a valid mime type at %s" % downloadUrl)

							os.unlink(localFilename)

browser.close()
vdisplay.stop()