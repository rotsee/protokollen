#!/usr/bin/env python2
#coding=utf-8
"""This script will delete a file and all of its documents,
   from both the storage, and the database.

   For each file, you need to provide its path fragments, if any, and name,
   e.g. `"Enköpings kommun", 3fce5e1f6db1bd90120a5e48e468a68b.pdf`

   You can use the command line, a file or a Google Spreadsheet document
   to provide the file(s) to be deleted.
"""

import settings

from modules.interface import Interface
from modules.datasheet import CSVFile, GoogleSheet, DataSet, HeaderlessDataSet
from modules.databases.debuggerdb import DebuggerDB


def main():
    """Entry point when run from command line.
    """
    command_line_args = [{
        "short": "-f", "long": "--file",
        "dest": "filename",
        "type": str,
        "help": """A headerless CSV file containing paths and names
                   of the files to delete."""
    }, {
        "short": "-p", "long": "--path",
        "dest": "path_fragments",
        "nargs": "+",
        "type": str,
        "help": """Path fragments and file name,
                   e.g. \"Enköpings kommun\" abcdefgh.pdf"""
    }, {
        "short": "-g", "long": "--google-sheet",
        "dest": "google_spreadsheet_key",
        "type": str,
        "help": """A Google Spreadsheet name, containing keys to be deleted.
                   The columns must contain (any) headers!"""
    }]
    ui = Interface(__file__,
                   """This script will delete a file and all of its documents,
                      from both the storage, and the database.""",
                   commandLineArgs=command_line_args)

    if ui.args.filename is not None:
        ui.info("Reading keys from `%s`" % ui.args.filename)
        data_set = CSVFile(ui.args.filename, has_headers=False)
    elif ui.args.google_spreadsheet_key is not None:
        ui.info("Reading keys from Google Spreadsheet`%s`" %
                ui.args.google_spreadsheet_key)
        data_set = GoogleSheet(
            ui.args.google_spreadsheet_key,
            settings.google_client_email,
            settings.google_p12_file)
    elif ui.args.path_fragments is not None:
        ui.info("Using key `%s`" % ui.args.path_fragments)
        data_set = HeaderlessDataSet([ui.args.path_fragments])
    else:
        ui.error("""You must specify either a file, a Google Spreadsheet,\
                    or a key. Run `./erase --help` for more info""")
        ui.exit()

    ui.info("Setting up db connection.")
    try:
        file_db = settings.Database(settings.db_server,
                                    settings.db_harvest_table,
                                    "info",
                                    port=settings.db_port)
        docs_db = settings.Database(settings.db_server,
                                    settings.db_extactor_table,
                                    "info",
                                    port=settings.db_port)
    except (TypeError, NameError, AttributeError):
        ui.info("No database setup found, using DebuggerDB")
        file_db = DebuggerDB(None, settings.db_harvest_table or "TABLE")
        docs_db = DebuggerDB(None, settings.db_extactor_table or "TABLE")

    ui.info("Connecting to file storage")
    file_storage = settings.Storage(settings.access_key_id,
                                    settings.secret_access_key,
                                    settings.access_token,
                                    settings.bucket_name)

    ui.info("Connecting to document storage")
    docs_storage = settings.Storage(settings.access_key_id,
                                    settings.secret_access_key,
                                    settings.access_token,
                                    settings.text_bucket_name)

    for row in data_set.get_next():
        path_fragments = row.list()  # ["Ale kommun", "abc.pdf"]
        db_key = file_db.create_key(path_fragments)  # "Ale kommun-abc.pdf"
        filename = path_fragments.pop()  # "abc.pdf"
        # path_fragments: ["Ale kommun"]
        file_path = file_storage.buildRemoteName(filename, path=path_fragments)
        file_path_from_db = file_db.get(db_key, "storage_path")

        # Double check that reconstructed file match matches that in db.
        # File paths was not always stored in db, so might very well be missing
        if file_path != file_path_from_db:
            ui.warning("File paths from storage and db do not match")
            ui.debug("Storage: %s; Db: %s" % (file_path, file_path_from_db))
            if not ui.ask_if_continue():
                ui.exit()
        docs = docs_db.get_attribute_with_value("file", db_key)
        if len(docs) == 0:
            message = "No documents for %s. Continue deleting only file?" % \
                      filename
            if not ui.ask_if_continue(message=message):
                ui.exit()
        file_db.delete(db_key)
        file_storage.delete_file(file_path)
        #for doc in docs:
        #   doc
        #   docs_storage.delete(create_key(get(doc, file)))


if __name__ == '__main__':
    main()
