#!/usr/bin/env python2
#coding=utf-8
import login
import pdfminer

from modules import interface
ui = interface.Interface(__file__,"Extracts text from files in an Amazon S3 bucket")
ui.info("Starting extractor")
ui.info("Connecting to S3")
import s3
filesConnection = s3.S3Connection(
		login.aws_access_key_id,
		login.aws_secret_access_key,
		login.aws_bucket_name)
from download import FileFromS3, FileType
for key in filesConnection.getNextFile():
	ui.info("Checking file %s" % key.name)
	fileFromS3 = FileFromS3(key, "temp/" + key.filename)
	if fileFromS3.success:
		if fileFromS3.getFileType() == FileType.PDF:
			ui.info("Starting pdf extraction")
			
			#PDF miner
		fileFromS3.delete()
		ui.exit()
	else:
		ui.warning("Failed to download %s from amazon S3!" % key.name)



