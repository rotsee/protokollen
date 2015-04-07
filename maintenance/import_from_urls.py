#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This will import files from a CSV with origins and URLs:

     Gnosjö kommun, http://www.gnosjo.se/documents/118763337687629933.pdf

   Run `./import_from_urls.py --help` for options.
"""

import settings

from modules.interface import Interface
from modules.protokollen import Files
from modules.datasheet import CSVFile
from modules.download import FileFromWeb
from urllib2 import HTTPError

commandline_args = [{
    "short": "-f", "long": "--file",
    "dest": "csv_file",
    "type": str,
    "help": """CSV file, each row on the format `origin, URL`"""
}, "overwrite", "tempdir"]
ui = Interface(__file__,
               """This script will import files from predefined URLs""",
               commandline_args=commandline_args)


def main():
    """Entry point when run from command line. """
    files_connection = Files(ui)
    csv_file = CSVFile(ui.args.csv_file, has_headers=False)
    for row in csv_file.get_next():
        origin = row["0"]
        url = row["1"]
        try:
            downloaded_file = FileFromWeb(url, "../temp/tempfile")
        except HTTPError:
            ui.warning("Url not found: %s" % url)
            continue
        files_connection.store_file(downloaded_file, origin, url)

if __name__ == '__main__':
    main()
