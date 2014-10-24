#!/usr/bin/env python2
#coding=utf-8
"""This is where we extract plain text and meta data from documents,
   and uploads it to Amazon and/or a database.
   The actual extraction is done by format-specific modules.
   Run `./extractor.py --help` for options.
"""

import login
import settings

from modules.interface import Interface
from modules.download import FileType
from modules.pdf import PdfExtractor
from modules.ooxml import DocxExtractor
from modules.doc import DocExtractor


def main():
    """Entry point when run from command line"""

    command_line_args = [{
      "short": "-o", "long": "--overwrite",
      "dest": "overwrite",
      "action": "store_true",
      "help": "Overwrite old files and database values."
      }]
    ui = Interface(__file__,
        "Extracts text from files in an Amazon S3 bucket",
        commandLineArgs=command_line_args)
    ui.info("Starting extractor")
    ui.info("Connecting to storage")
    source_files_connection = settings.Storage(login.aws_access_key_id,
                                               login.aws_secret_access_key,
                                               login.aws_access_token,
                                               login.aws_bucket_name)

    if ui.executionMode < Interface.DRY_MODE:
        uploader = settings.Storage(login.aws_access_key_id,
                                    login.aws_secret_access_key,
                                    login.aws_access_token,
                                    login.aws_text_bucket_name)

    for key in source_files_connection.getNextFile():
        # first of all, check if the processed file already exists in
        # remote storage (no need to do expensive PDF processing if it
        # is.
        if ui.executionMode < Interface.DRY_MODE:
            remoteFilename = uploader.buildRemoteName(
                  key.basename,
                  ext="txt",
                  path=key.path_fragments)
            if (uploader.fileExists(remoteFilename) and
                not ui.args.overwrite):
                continue #File is already in remote storage

        ui.info("Processing file %s" % key.name)
        try:
            downloaded_file = source_files_connection.getFile(key, "temp/"+key.filename)
        except Exception as e:
            ui.warning("Could not download %s from storage: %s: %s" %
                       (key.name, type(e), e))
            continue

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
        else:
            raise ValueError("No extractor for filetype %s" % filetype)

        print extractor.path
        print extractor.text

        try:
            text = extractor.get_text()
            #uploader.putFileFromString(text, remoteFilename)
        except Exception as e:
            ui.error("Could not get text from file %s " % key.name)

        try:
            meta = extractor.get_metadata()
            print meta.data
        except Exception as e:
            print e
            ui.error("Could not get metadata from file %s " % key.name)

        try:
            text = extractor.get_date()
            print key.path_fragments,
            print date
        except Exception as e:
            ui.error("Could not get date from file %s " % key.name)

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
