#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This will import files from a a Dropbox storage,
   put them in the default storage and index them in the DB.
   This is useful for manually adding files.

   Run `./harvest_from_storage.py --help` for options.
"""

import settings

from modules.protokollen import Files
from modules.interface import Interface
from modules.storage import DropboxStorage

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
    "short": "-p", "long": "--path",
    "default": "/",
    "type": str,
    "help": "Folder path to look (recursively) in at Dropbox.",
    "dest": "path",
}, "overwrite"]
ui = Interface(__file__,
               """This script will import files from a custom
                  storage, and add them to the Protokollen
                  file storage(s) and database(s).""",
               commandline_args=commandline_args)


def main():
    """Entry point when run from command line."""

    ui.info("Setting up DB and storage connection")
    files_connection = Files(ui)

    ui.info("Connecting to Dropbox storage")
    source = DropboxStorage(settings.dropbox_key,
                            settings.dropbox_secret,
                            token=settings.dropbox_token,
                            path=ui.args.path)

    local_file = "../temp/tempfile"

    for file_ in source.get_next_file():

        download_file = source.get_file(file_, local_file)
        origin = file_.path_fragments[ui.args.source_fragment]

        files_connection.store_file(download_file, origin, None)

        try:
            download_file.delete()
        except Exception as e:
            ui.warning("Could not delete temp file %s (%s)" %
                       (local_file, e))


if __name__ == '__main__':
    main()
