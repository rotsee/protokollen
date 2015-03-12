#!/usr/bin/env python2
# coding=utf-8
"""An extract.py fork, that extracts documents from a single,
   local file. This script is useful for debugging. It does
   not store anything in the databases or storages.
"""

import settings

from modules.interface import Interface
from modules.download import File
from modules.databases.debuggerdb import DebuggerDB
from modules.documents import DocumentList


def main():
    """Entry point when run from command line"""

    command_line_args = [{
        "short": "-f", "long": "--file",
        "type": str, "dest": "file",
        "help": "File to extract document(s) from."
    }]
    ui = Interface(__file__,
                   "Extracts text and metadata from a local file",
                   commandLineArgs=command_line_args)

    ui.info("Connecting to storage")
#    docs_connection = settings.Storage(settings.access_key_id,
#                                       settings.secret_access_key,
#                                       settings.access_token,
#                                       settings.text_bucket_name)

    # Setup database for indexing uploaded files,
    # and storing metadata
 #   ui.info("Connecting to databases")
 #   try:
 #       docs_db = settings.Database(settings.db_server,
 #                                   settings.db_extactor_table,
 #                                   "info",
 #                                   port=settings.db_port)
#        docs_db = DebuggerDB("server", "table")
 #   except (TypeError, NameError, AttributeError) as e:
 #       ui.info("No database setup found, using DebuggerDB (%s)" % e)
    docs_db = DebuggerDB(None, settings.db_extactor_table or "TABLE")

    ui.info("Opening file %s" % ui.args.file)
    try:
        local_file = File(ui.args.file)
    except Exception as e:
        ui.warning("Could not open file %s. %s" % (ui.args.file, e))
        exit()

    extractor = local_file.extractor()
    extractor_type = type(extractor).__name__
    if extractor_type == "HtmlExtractor":
        extractor.content_xpath = ui.args.html

    # for page in extractor.get_next_page():
    #     print "NEXT PAGE --------------------------------------------------"
    #     print page.get_header()

    document_list = DocumentList(extractor)
    for document in document_list.get_next_document():
        print "---------------------------------------------"
        print "type",
        print document.type_
        print "date",
        print document.date
        print "len",
        print len(document)
        print document.header

    ui.exit()

if __name__ == '__main__':
    main()
