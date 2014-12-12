#!/usr/bin/env python2
#coding=utf-8
"""This script will delete a file and all of its documents,
   from both the storage, and the database.

   You can give the filename (key) directly, or use a file
   containg one key on each line, or use a Google Spreadsheet.
   The spreadsheet should contain all filename in one column,
   and the column must contain a header (any header will do).
"""

import settings

from modules.interface import Interface
from modules.datasheet import CSVFile, GoogleSheet, DataSet
from modules.databases.debuggerdb import DebuggerDB


def main():
    """Entry point when run from command line.
    """
    command_line_args = [{
        "short": "-f", "long": "--file",
        "dest": "filename",
        "type": str,
        "help": """File containing a new-line separated list of
                   keys to be deleted."""
    }, {
        "short": "-k", "long": "--key",
        "dest": "key",
        "type": str,
        "help": "A key to be deleted."
    }, {
        "short": "-g", "long": "--google-sheet",
        "dest": "google_spreadsheet_key",
        "type": str,
        "help": """A Google Spreadsheet name, containing keys to be deleted.
                   The column must contain a (any) header!"""
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
    elif ui.args.key is not None:
        ui.info("Using key `%s`" % ui.args.key)
        data_set = DataSet([{"key": ui.args.key}])
    else:
        ui.error("""You must specify either a file,
                    a Google Spreadsheet, or a key""")
        ui.exit()

    for row in data_set.get_next():
        print row.itervalues().next()
    ui.exit()

    ui.info("Setting up db connection.")
    try:
        db = settings.Database(settings.db_server,
                               settings.db_harvest_table,
                               "info",
                               port=settings.db_port
                               )
    except (TypeError, NameError, AttributeError):
        ui.info("No database setup found, using DebuggerDB")
        db = DebuggerDB(None, settings.db_harvest_table or "TABLE")

    ui.info("Connecting to file storage")
    storage = settings.Storage(settings.access_key_id,
                               settings.secret_access_key,
                               settings.access_token,
                               settings.bucket_name)


if __name__ == '__main__':
    main()
