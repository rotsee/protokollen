#!/usr/bin/env python2
#coding=utf-8
"""This is where we extract plain text and meta data from files,
   and upload it to a storage and/or a database.
   File content will be split up in documents, if multiple
   document types are detected within one file (e.g. agenda,
   minutes and attachments) .

   The actual extraction is done by format-specific modules.
   Run `./extractor.py --help` for options.
"""

import settings

from os import path

from modules.interface import Interface
from modules.databases.debuggerdb import DebuggerDB


def parse_rules(tuple_, header):
    """
     Parse document rules. See settings.py for syntax
    """
    rule_key = tuple_[0].upper()
    rule_val = tuple_[1]
    header = header.upper()
    if rule_key == "AND":
        hit = True
        for rule in rule_val:
            hit = hit and parse_rules(rule, header)
        return hit
    elif rule_key == "OR":
        hit = False
        for rule in rule_val:
            hit = hit or parse_rules(rule, header)
        return hit
    elif rule_key == "NOT":
        hit = not parse_rules(rule_val, header)
        return hit
    elif rule_key == "HEADER_CONTAINS":
        return header.find(rule_val.upper()) > -1


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
    source_files_connection = settings.Storage(settings.access_key_id,
                                               settings.secret_access_key,
                                               settings.access_token,
                                               settings.bucket_name)
    destination_files_connection = settings.Storage(settings.access_key_id,
                                                    settings.secret_access_key,
                                                    settings.access_token,
                                                    settings.text_bucket_name)

    # Setup database for indexing uploaded files,
    # and storing metadata
    ui.info("Connecting to database")
    try:
        db = settings.Database(settings.db_server,
                               settings.db_extactor_table,
                               "info",
                               port=settings.db_port
                               )
    except (TypeError, NameError, AttributeError) as e:
        ui.info("No database setup found, using DebuggerDB")
        db = DebuggerDB(None, settings.db_extactor_table or "TABLE")

    for key in source_files_connection.get_next_file():
        # first of all, check if the processed file already exists in
        # remote storage (no need to do expensive PDF processing if it
        # is.
        if ui.executionMode < Interface.DRY_MODE:
            remote_filename = destination_files_connection.buildRemoteName(
                key.basename,
                ext="txt",
                path=key.path_fragments)
            if (destination_files_connection.prefix_exists(remote_filename) and
                    not ui.args.overwrite):
                continue  # File is already in remote storage

        ui.info("Fetching file %s" % key.name)
        try:
            temp_filename = path.join("temp", key.filename)
            downloaded_file = source_files_connection.getFile(key,
                                                              temp_filename)
        except Exception as e:
            ui.warning("Could not fetch %s from storage: %s: %s" %
                       (key.name, type(e), e))
            continue

        dbkey = db.create_key([key.path, key.filename])

        extractor = downloaded_file.extractor()
        ui.info("Extracting text with %s from %s" %
                (extractor.__class__.__name__, downloaded_file.localFile))

        db.put(dbkey, "text", extractor.get_text())

        for page in extractor.get_next_page():
            page_date = page.get_date() or extractor.get_date()
            db.put(dbkey, "meeting_date", page_date)
            page_header = page.get_header() or extractor.get_header()
            db.put(dbkey, "header", page_header)

            page_type = None
            for document_type in settings.document_rules:
                if parse_rules(document_type[1], page_header.text):
                    page_type = document_type[0]
            db.put(dbkey, "document_type", page_type)

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
