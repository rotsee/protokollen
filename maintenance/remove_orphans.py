#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This script will remove files without database entries,
   and database entries without a corresponding file.
"""

import settings

from modules.interface import Interface


def main():
    """Entry point when run from command line"""

    ui = Interface(__file__,
                   "Removes files w/o db entries and vice versa",
                   commandline_args=["limit"])

    ui.info("Connecting to file storage")
    file_storage = settings.Storage(settings.access_key_id,
                                    settings.secret_access_key,
                                    settings.access_token,
                                    settings.bucket_name)

    ui.info("Connecting to file database")
    file_db = settings.Database(settings.db_server,
                                settings.db_harvest_table,
                                "info",
                                port=settings.db_port)

    counter = {
        "files_wo_db": 0,
        "files_wo_storage": 0,
        "docs_wo_db": 0,
        "files_wo_storage": 0,
        "docs_wo_files": 0
    }

    # Check for each file in storage that it has a db entry
    for key in file_storage.get_next_file():

        files_dbkey = file_db.create_key(key.path_fragments + [key.filename])
        ui.debug("files_dbkey: %s" % files_dbkey)  # "Ale kommun-xxx.pdf"

        if not file_db.exists(files_dbkey):
            ui.info("File db data missing for file %s" % key)
            counter["files_wo_db"] += 1
            if (ui.args.limit is not None
               and counter["files_wo_db"] > ui.args.limit - 1):
                break

            ui.info("Deleting file")
            if ui.executionMode < Interface.DRY_MODE:
                file_storage.delete_file(key)
            ui.info("Deleting docs from storage")
            if ui.executionMode < Interface.DRY_MODE:
                pass
            ui.info("Deleting docs from db")
            if ui.executionMode < Interface.DRY_MODE:
                pass

    print("Deleted %d files w/o database entry" % counter["files_wo_db"])
    print("Deleted %d file entries w/o file" % counter["files_wo_storage"])
    print("Deleted %d documents w/o database entry" % counter["docs_wo_db"])
    print("Deleted %d document entries w/o file" % counter["files_wo_storage"])
    print("Deleted %d documents w/o file" % counter["docs_wo_files"])

if __name__ == '__main__':
    main()
