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
                   "Removes files w/o db entries and vice versa")

    ui.info("Connecting to file storage")
    files_connection = settings.Storage(settings.access_key_id,
                                        settings.secret_access_key,
                                        settings.access_token,
                                        settings.bucket_name)

    ui.info("Connecting to file database")
    files_db = settings.Database(settings.db_server,
                                 settings.db_harvest_table,
                                 "info",
                                 port=settings.db_port)
if __name__ == '__main__':
    main()
