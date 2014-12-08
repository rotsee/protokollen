#!/usr/bin/env python2
#coding=utf-8
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


def get_document_type(header_text):
    """
     Return the first matching document type, based on this
     header text.
    """
    for document_type in settings.document_rules:
        if parse_rules(document_type[1], header_text):
            return document_type[0]


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
                                     port=settings.db_port
                                     )
        text_db = settings.Database(settings.db_server,
                                    settings.db_extactor_table,
                                    "info",
                                    port=settings.db_port
                                    )
    except (TypeError, NameError, AttributeError) as e:
        ui.info("No database setup found, using DebuggerDB")
        files_db = None
        text_db = DebuggerDB(None, settings.db_extactor_table or "TABLE")

    for key in files_connection.get_next_file():
        # first of all, check if the processed file already exists in
        # remote storage (no need to do expensive PDF processing if it
        # is.
        if ui.executionMode >= Interface.DRY_MODE:
            continue

        prefix = docs_connection.buildRemoteName(key.basename,
                                                 path=key.path_fragments)
        """ "Ale kommun/xxx" """
        files_dbkey = files_db.create_key(key.path_fragments + [key.filename])
        """ "Ale kommun-xxx.pdf" """
        file_data = files_db.get_attribute_with_value("_id", files_dbkey)

        if (docs_connection.prefix_exists(prefix) and
                len(file_data) > 0 and
                not ui.args.overwrite):
            ui.debug("Documents already extracted for file %s (%s)" %
                     (prefix, files_dbkey))
            continue

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
        ui.info("Extracting text with %s from %s" %
                (extractor.__class__.__name__, downloaded_file.localFile))

        last_page_type = None
        last_page_date = None
        documents = []
        for page in extractor.get_next_page():
            page_text = page.get_text()
            page_header = page.get_header() or extractor.get_header()
            page_type = get_document_type(page_header)
            page_date = page.get_date() or extractor.get_date()

            if len(documents) > 0 and\
               page_type == last_page_type and\
               page_date == last_page_date:
                documents[-1]["text"] = documents[-1]["text"] + page_text
            else:
                documents.append({
                    "text": page_text,
                    "header": page_header,
                    "date": page_date,
                    "type": page_type
                })

            last_page_type = page_type
            last_page_date = page_date

        i = 0
        for document in documents:
            i += 1
            text_dbkey = text_db.create_key([key.path, i, key.filename])
            text_db.put(text_dbkey, "meeting_date", document["date"])
            text_db.put(text_dbkey, "header", document["header"])
            text_db.put(text_dbkey, "source", key.path)
            text_db.put(text_dbkey, "text", document["text"])
            text_db.put(text_dbkey, "document_type", page_type)

            remote_filename = docs_connection.buildRemoteName(
                key.filename,
                ext="txt",
                path=key.path_fragments + [str(i)])
            docs_connection.put_file_from_string(document["text"],
                                                 remote_filename)

        downloaded_file.delete()

    ui.exit()

if __name__ == '__main__':
    main()
