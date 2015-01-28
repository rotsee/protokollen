#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This will import files from a a Dropbox storage,
   put them in the default storage and index them in the DB.
   This is useful for manually adding files.

   Run `./harvest_from_storage.py --help` for options.
"""

import settings

from hashlib import md5

from modules.interface import Interface
from modules.storage import DropboxStorage
from modules.databases.debuggerdb import DebuggerDB
from modules.utils import make_unicode

############# GLOBAL VARIABLES ###############
commandline_args = [{
    "short": "-f", "long": "--source-from-fragment",
    "dest": "source_fragment",
    "default": -1,
    "type": int,
    "help": """What part of the path contains the source name?
               The first path framnent is 0. E.g. 2 to use `Arboga`
               in `/files/municipalities/Arboga/`.
               You can also use -1, to start from the end."""
}, {
    "short": "-o", "long": "--overwrite",
    "action": "store_true",
    "default": False,
    "dest": "overwrite",
    "help": "Should existing files and database entries be overwritten?"
}]
ui = Interface(__file__,
               """This script will import files from a custom
                  storage, and add them to the Protokollen
                  file storage(s) and database(s).""",
               commandLineArgs=commandline_args)
##############################################


def main():
    """Entry point when run from command line.
       Variables:
        * db: A Database object, as defined in settings.py
        * dest_storage: A storage, as defined in settings.py
        * source: A storage holding files to be imported
    """
    ui.info("Setting up db connection for storing data on downloaded files.")
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
    dest_storage = settings.Storage(settings.access_key_id,
                                    settings.secret_access_key,
                                    settings.access_token,
                                    settings.bucket_name)

    source = DropboxStorage(settings.dropbox_key,
                            settings.dropbox_secret,
                            token=settings.dropbox_token,
                            path="/Kommuner")

    for file_ in source.get_next_file():
        try:
            filename = md5(file_.name).hexdigest()
        except UnicodeDecodeError:
            filename = md5(make_unicode(file_.name)).hexdigest()
        filename = md5(file_.name).hexdigest()
        local_filename = "temp/" + filename
        download_file = source.get_file(file_, local_filename)
        source_fragment = file_.path_fragments[ui.args.source_fragment]

        filetype = download_file.get_file_type()
        file_ext = download_file.get_file_extension()
        remote_name = dest_storage.buildRemoteName(filename,
                                                   path=source_fragment,
                                                   ext=file_ext)
        """ Remote file name is created from source and filename"""
        dbkey = db.create_key([source_fragment, filename + "." + file_ext])
        """ Database key is created from source and filename"""

        # Check if a file with this name exists
        # in both storage and DB
        if (dest_storage.prefix_exists(remote_name) and
           db.exists(dbkey) is not None and
           ui.args.overwrite is not True):
            ui.debug("%s already exists, not overwriting" % url)
        else:
            if filetype in settings.allowedFiletypes:
                ui.info("Storing %s" % local_filename)
                dest_storage.put_file(local_filename, remote_name)

                ui.debug("Storing file data in database")
                db.put(dbkey, u"origin", file_.basename)

                # Should rather be the more generic “source”
                db.put(dbkey, u"municipality", source_fragment)
                #print "municipality: %s" % source_fragment
                db.put(dbkey, u"file_type", file_ext)
                #print "file_type: %s" % file_ext
                db.put(dbkey, u"storage_path", remote_name)
                #print "storage_path: %s" % remote_name
                db.put(dbkey, u"harvesting_rules", None)
                try:
                    ui.debug("Extracting metadata")
                    extractor = download_file.extractor()
                    meta = extractor.get_metadata()
                    ui.debug(meta.data)
                    db.put(dbkey, u"metadata", meta.data, overwrite=ui.args.overwrite)
                    #print meta.data
                except Exception as e:
                    ui.warning("Could not get metadata from %s. %s" % (dbkey, e))

            else:
                ui.warning("%s is not an allowed mime type or download failed"
                           % download_file.mimeType)
        try:
            download_file.delete()
        except Exception as e:
            ui.warning("Could not delete temp file %s (%s)" % (local_filename, e))


if __name__ == '__main__':
    main()
