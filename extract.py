#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This is where we extract plain text and textual meta data from files,
   and upload it to a storage and/or a database.
   File content will be split up in documents, if multiple
   document types are detected within one file (e.g. agenda,
   minutes and attachments).

   The actual extraction is done by format-specific modules.
   Run `./extractor.py --help` for options.
"""

import settings

from os import path

from modules.interface import Interface
from modules.databases.debuggerdb import DebuggerDB
from modules.documents import DocumentList, document_headers
from modules.extractors.documentBase import ExtractionNotAllowed


def main():
    """Entry point when run from command line"""

    command_line_args = [{
        "short": "-o",
        "long": "--overwrite",
        "dest": "overwrite",
        "action": "store_true",
        "help": "Overwrite old files and database values."
    }, {
        "short": "-f",
        "long": "--from",
        "dest": "start_from",
        "type": str,
        "help": "What file to start extracting from."
    }]
    ui = Interface(__file__,
                   "Extracts text and metadata from files",
                   commandline_args=command_line_args)

    ui.info("Connecting to storage")
    files_connection = settings.Storage(settings.access_key_id,
                                        settings.secret_access_key,
                                        settings.access_token,
                                        settings.bucket_name)
    docs_connection = settings.Storage(settings.access_key_id,
                                       settings.secret_access_key,
                                       settings.access_token,
                                       settings.text_bucket_name)

    # Setup database for indexing uploaded files,
    # and storing metadata
    ui.info("Connecting to databases")
    try:
        files_db = settings.Database(settings.db_server,
                                     settings.db_harvest_table,
                                     "info",
                                     port=settings.db_port)
        docs_db = settings.Database(settings.db_server,
                                    settings.db_extactor_table,
                                    "info",
                                    port=settings.db_port)
    except (TypeError, NameError, AttributeError) as e:
        ui.info("No database setup found, using DebuggerDB (%s)" % e)
        files_db = None
        docs_db = DebuggerDB(None, settings.db_extactor_table or "TABLE")

    keep_waiting = (ui.args.start_from is not None)

    for key in files_connection.get_next_file():

        # Are we waiting for a certain key before starting?
        if keep_waiting is True:
            if key.name == ui.args.start_from.decode("utf8"):
                keep_waiting = False
            else:
                continue

        # first of all, check if the processed file already exists in
        # remote storage (no need to do expensive PDF processing if it
        # is.
        prefix = docs_connection.buildRemoteName(key.basename,
                                                 path=key.path_fragments)
        """ "Ale kommun/xxx" """
        ui.debug("file prefix: %s" % prefix)

        files_dbkey = files_db.create_key(key.path_fragments + [key.filename])
        """ "Ale kommun-xxx.pdf" """
        ui.debug("files_dbkey: %s" % files_dbkey)

        if not files_db.exists(files_dbkey):
            ui.warning("File db data missing for file %s" % key)
            continue

        existing_docs_data = docs_db.get_attribute_with_value("file_key",
                                                              files_dbkey)
        if (docs_connection.prefix_exists(prefix) and
                existing_docs_data is not None and
                not ui.args.overwrite):
            ui.debug("Documents already extracted for file %s (%s)" %
                     (prefix, files_dbkey))
            continue

        downloaded_file = None
        ui.info("Fetching file %s" % key.name)
        try:
            temp_filename = path.join("temp", key.filename)
            downloaded_file = files_connection.get_file(key,
                                                        temp_filename)
        except Exception as e:
            ui.warning("Could not fetch %s from storage: %s: %s" %
                       (key.name, type(e), e))
            continue

        file_type = downloaded_file.get_file_type()
        if file_type not in settings.allowedFiletypes:
            ui.warning("Filetype %s is not allowed in settings.py" % file_type)
            continue

        extractor = downloaded_file.extractor()
        extractor_type = type(extractor).__name__
        if extractor_type == "HtmlExtractor":
            harvesting_rules = files_db.get(files_dbkey, "harvesting_rules")
            extractor.content_xpath = harvesting_rules["html"]
            ui.debug("HTML file. Content is in %s" % extractor.content_xpath)

        ui.info("Extracting from %s with %s" % (downloaded_file.localFile,
                                                extractor_type))
        try:
            document_list = DocumentList(extractor)
        except ExtractionNotAllowed:
            ui.warning("Exraction not allowed for %s" % key.name)
            # Continue without deleting. We might want to inspect this file
            continue
        i = 0
        # FIXME: let DocumentList keep track of this
        for document in document_list.get_next_document():
            i += 1
            remote_filename = docs_connection.buildRemoteName(
                str(i),
                ext="txt",
                path=key.path_fragments + [key.filename])
            """ "Ale kommun/xxx/1.txt" """
            docs_dbkey = docs_db.create_key([key.path, key.filename, str(i)])

            if ui.executionMode >= Interface.DRY_MODE:
                print "docs_dbkey"
                print docs_dbkey
                print "document_type",
                print document.type_
                print "meeting_date",
                print document.date
                print "source",
                print files_db.get(files_dbkey, u"origin")
                print "origin",
                print files_db.get(files_dbkey, u"municipality")
                print "text_file",
                print remote_filename
                print "original file",
                print files_dbkey
                print "text length",
                print len(document.text)
                continue
            """ "Ale kommun-xxx-1" """
            docs_db.put(docs_dbkey, "meeting_date", document.date)
            docs_db.put(docs_dbkey, "file_key", files_dbkey)
            docs_db.put(docs_dbkey, "file", key.name)
            docs_db.put(docs_dbkey, "header", document.header)
            docs_db.put(docs_dbkey, "text_file", remote_filename)
            docs_db.put(docs_dbkey, "text", document.text)
            docs_db.put(docs_dbkey, "document_type", document.type_)
            # Original URL, if any
            docs_db.put(docs_dbkey, "source",
                        files_db.get(files_dbkey, u"origin"))
            # NB We use a different, but more logical naming scheme for docs
            docs_db.put(docs_dbkey, "origin",
                        files_db.get(files_dbkey, u"municipality"))

            docs_connection.put_file_from_string(document.text,
                                                 remote_filename,
                                                 headers=document_headers)

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
