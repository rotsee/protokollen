# -*- coding: utf-8 -*-
"""This module contains high-level functions for handling
   “files” and “documents”, and should be used by all scripts
   that want to store, fetch or erase stuff.

   Use settings.py to select database and storage.
"""

import settings
from modules.databases.debuggerdb import DebuggerDB
from modules.download import FileType
from modules.utils import md5sum


class Files(object):
    """Handles all interaction with file storage and file database.
    """

    def __init__(self, ui):
        """ui is an modules.interface.Interface"""

        self.ui = ui
        self.overwrite = ui.args.overwrite or False

        try:
            self.ui.info("Setting up file db connection.")
            self.db = settings.Database(settings.db_server,
                                        settings.db_harvest_table,
                                        "info",
                                        port=settings.db_port)
        except (TypeError, NameError, AttributeError):
            self.ui.info("No database setup found, using DebuggerDB")
            self.db = DebuggerDB(None, settings.db_harvest_table or "TABLE")

        self.storage = settings.Storage(settings.access_key_id,
                                        settings.secret_access_key,
                                        settings.access_token,
                                        settings.bucket_name)

    def exists(self, path, filename, extension):
        """Return True of this file exists in both the storage
           and the database"""
        filekey = self.storage.buildRemoteName(filename,
                                               path=path,
                                               ext=extension)
        dbkey = self.db.create_key([path, filename + "." + extension])

        return (self.storage.prefix_exists(filekey) and
                self.db.exists(dbkey))

    def store_file(self, local_filename, filetype, origin, source,
                   harvesting_rules=None, overwrite=False):
        """origin and filetype is used for consistent naming.
           A hash value for the filename can be used for backwards
           compatibility when checking if a file already exists.

           `origin` is the full name of a municipality (Gnosjö kommun)
           `source` is the URL this file was harvested from, if any
        """

        if filetype not in settings.allowedFiletypes:
            self.ui.info("%s is not an allowed file type" % filetype)
            return

        filename = md5sum(local_filename)

        if self.exists(origin, filename, filetype) and not overwrite:
            self.ui.debug("Not overwriting %s/%s" % (origin, filename))
            return

        remote_name = self.storage.buildRemoteName(filename,
                                                   path=origin,
                                                   ext=filetype)
        dbkey = self.db.create_key([origin, filename + "." + filetype])

        self.ui.info("Storing %s in storage" % local_filename)
        self.storage.put_file(local_filename, remote_name)

        self.ui.debug("Storing %s in database" % local_filename)
        # Should rather be the more exact “source”
        self.db.put(dbkey, u"origin", source)  # URL
        # Should rather be the more generic “origin”
        self.db.put(dbkey, u"municipality", origin)
        self.db.put(dbkey, u"file_type", filetype)
        self.db.put(dbkey, u"storage_path", remote_name)
        self.db.put(dbkey, u"harvesting_rules", harvesting_rules)
        try:
            self.ui.debug("Extracting metadata")
            type_ = FileType.ext_to_type_dict[filetype]
            extractor = FileType.type_to_extractor_dict[type_].extractor()
            meta = extractor.get_metadata()
            self.db.put(dbkey, u"metadata", meta.data, overwrite=overwrite)
        except Exception as e:
            self.ui.info("Could not get metadata from %s. %s" % (dbkey, e))

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
