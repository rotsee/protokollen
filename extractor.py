#!/usr/bin/env python2
#coding=utf-8
import login
from modules.interface import Interface
from modules.s3 import S3Connection

from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

def convert_pdf(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

    fp = file(path, 'rb')
    process_pdf(rsrcmgr, device, fp)
    fp.close()
    device.close()

    str = retstr.getvalue()
    retstr.close()
    return str

ui = Interface(__file__, "Extracts text from files in an Amazon S3 bucket")
ui.info("Starting extractor")
ui.info("Connecting to S3")
filesConnection = S3Connection(
		login.aws_access_key_id,
		login.aws_secret_access_key,
		login.aws_bucket_name)
from download import FileFromS3, FileType
for key in filesConnection.getNextFile():
	ui.info("Processing file %s" % key.name)
	downloaded_file = FileFromS3(key, "temp/" + key.filename)
	if downloaded_file.success:
		if downloaded_file.getFileType() == FileType.PDF:
			ui.info("Starting pdf extraction")			
			#PDF miner
			print convert_pdf(downloaded_file.localFile)
		downloaded_file.delete()
		ui.exit()
	else:
		ui.warning("Failed to download %s from amazon S3!" % key.name)



