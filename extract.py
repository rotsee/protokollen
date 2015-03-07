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
from modules.documents import DocumentList


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

    for key in files_connection.get_next_file():
        # first of all, check if the processed file already exists in
        # remote storage (no need to do expensive PDF processing if it
        # is.

        prefix = docs_connection.buildRemoteName(key.basename,
                                                 path=key.path_fragments)
        """ "Ale kommun/xxx" """
        files_dbkey = files_db.create_key(key.path_fragments + [key.filename])
        """ "Ale kommun-xxx.pdf" """
        file_data = files_db.get_attribute_with_value("_id", files_dbkey)
        file_data = (file_data or [None])[0]  # Get first hit, should be one
        if file_data is None:
            ui.warning("File db data missing for file %s" % key)
            continue
        else:
            file_data = file_data[u"_source"]

        old_docs_data = docs_db.get_attribute_with_value("file_key",
                                                         files_dbkey)
        if (docs_connection.prefix_exists(prefix) and
                len(old_docs_data) > 0 and
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

        extractor = downloaded_file.extractor()
        extractor_type = type(extractor).__name__
        if extractor_type == "HtmlExtractor":
            extractor.content_xpath = file_data["harvesting_rules"]["html"]
            ui.debug("HTML file. Content is in %s" % extractor.content_xpath)

        ui.info("Extracting from %s with %s" % (downloaded_file.localFile,
                                                extractor_type))
        document_list = DocumentList(extractor)
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
                print file_data[u"origin"]
                print "origin",
                print file_data[u"municipality"]
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
            if u"origin" in file_data:
                # Original URL, if any
                docs_db.put(docs_dbkey, "source", file_data[u"origin"])
            # NB We use a different, but more logical naming scheme for docs
            docs_db.put(docs_dbkey, "origin", file_data[u"municipality"])

            docs_connection.put_file_from_string(document.text,
                                                 remote_filename)

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
