#!/usr/bin/env python2
#coding=utf-8
"""This is where we extract plain text and meta data from documents,
   and uploads it to Amazon and/or a database.
   The actual extraction is done by format-specific modules.
   Run `./extractor.py --help` for options.
"""

import login
from modules.interface import Interface
from modules.s3 import S3Connection
from modules.download import FileFromS3, FileType
from modules.pdf import PdfExtractor
from modules.ooxml import DocxExtractor
from modules.doc import DocExtractor


def main():
	"""Entry point when run from command line"""
	ui = Interface(__file__, "Extracts text from files in an Amazon S3 bucket")
	ui.info("Starting extractor")
	ui.info("Connecting to S3")
	source_files_connection = S3Connection(
			login.aws_access_key_id,
			login.aws_secret_access_key,
			login.aws_bucket_name)
	for key in source_files_connection.getNextFile():
		ui.info("Processing file %s" % key.name)
		try:
			downloaded_file = FileFromS3(key, "temp/"+key.filename)
		except:
			ui.warning("Could not download %s from Amazon" % key.name)
			continue
		text = None
		filetype = downloaded_file.getFileType()
		if filetype == FileType.PDF:
			ui.info("Starting pdf extraction from %s" % downloaded_file.localFile)
			extractor = PdfExtractor(downloaded_file.localFile)
		elif filetype == FileType.DOCX:
			ui.info("Starting docx extraction from %s" % downloaded_file.localFile)
			extractor = DocxExtractor(downloaded_file.localFile)
		elif filetype == FileType.DOC:
			ui.info("Starting doc extraction from %s" % downloaded_file.localFile)
			extractor = DocExtractor(downloaded_file.localFile)
			
		text = extractor.getText()
		meta = extractor.getMetadata()
		print meta.data
		downloaded_file.delete()

		ui.exit()

if __name__ == '__main__':
    main()
