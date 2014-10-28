#!/usr/bin/env python2
#coding=utf-8
"""This is where we extract plain text and meta data from documents,
   and upload it to a storage and/or a database.
   The actual extraction is done by format-specific modules.
   Run `./extractor.py --help` for options.
"""

import login
import settings

from os import path

from modules.interface import Interface
from modules.download import FileType
from modules.extractors.pdf import PdfExtractor
from modules.extractors.ooxml import DocxExtractor
from modules.extractors.doc import DocExtractor


def main():
    """Entry point when run from command line"""

    command_line_args = [{
        "short": "-o",
        "long": "--overwrite",
        "dest": "overwrite",
        "action": "store_true",
        "help": "Overwrite old files and database values."
    }]
    ui = Interface(__file__,
                   "Extracts text and metadata from files",
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
            remote_filename = uploader.buildRemoteName(
                key.basename,
                ext="txt",
                path=key.path_fragments)
            if (uploader.fileExists(remote_filename) and
                    not ui.args.overwrite):
                continue  # File is already in remote storage

        ui.info("Fetching file %s" % key.name)
        try:
            temp_filename = path.join("temp", key.filename)
            downloaded_file = source_files_connection.getFile(
                key,
                temp_filename)
        except Exception as e:
            ui.warning("Could not fetch %s from storage: %s: %s" %
                       (key.name, type(e), e))
            continue

        filetype = downloaded_file.getFileType()
        if filetype == FileType.PDF:
            ui.info("Extracting text from pdf: %s" % downloaded_file.localFile)
            extractor = PdfExtractor(temp_filename)
        elif filetype == FileType.DOCX:
            ui.info("Extracting text from docx %s" % downloaded_file.localFile)
            extractor = DocxExtractor(downloaded_file.localFile)
        elif filetype == FileType.DOC:
            ui.info("Extracting text from doc %s" % downloaded_file.localFile)
            extractor = DocExtractor(downloaded_file.localFile)
        else:
            raise ValueError("No extractor for filetype %s" % filetype)

#        try:
#            text = extractor.get_text()
#            uploader.putFileFromString(text, remote_filename)
#        except Exception as e:
#            ui.error("Could not get text from file %s " % key.name)

        try:
            meta = extractor.get_metadata()
            print meta.data
        except Exception as e:
            print e
            ui.error("Could not get metadata from file %s " % key.name)

        try:
            fallback_date = extractor.get_date()
            print fallback_date
        except Exception as e:
            ui.error("Could not get date from file %s " % key.name)

        for page in extractor.get_next_page():
            page_date = page.get_date() or fallback_date
            page_header = page.get_header().upper()
            page_type = 0

            if page_header.find("PROTOKOLL") or\
               page_header.find("SAMMANTRÄDE"):
                if page_header.find("KOMMUNSTYRELSE"):
                    page_type = 1

            print page_type
            print page_date

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
