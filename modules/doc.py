#coding=utf-8
"""This module includes tools for handling and extracting text from
   old Microsoft Word (.doc) files. It uses the wv library
"""

from documentBase import ExtractorBase

import subprocess
from modules.metadata import Metadata

def run_command(command):
    """Runs a shell command and captures stdout.
       This is for wvText (and very hackish).
       We should probably rather let wv write to a file.
    """
    process = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         shell=True)
    return iter(process.stdout.readline, b'')

class DocExtractor(ExtractorBase):
    """Class for getting plain text from a Microsoft Word file.
    """

    def get_metadata(self):
        """Returns a .modules.metadata.Metadata object
        """
        command = 'wvSummary ' + self.path
        metadata = Metadata()
        for line in run_command(command):
            parts = line.strip().replace("\"", "").split(" = ")
            if len(parts) == 2:
                metadata.add({parts[0]: parts[1]}, "mso")
        return metadata


    def get_text(self):
        """Returns all text content from the document as plain text.
        """
        out = ' /dev/stdout' #ugly, ugly hack. Will only work on *nix
        command = 'wvText ' + self.path + out
        string = ""
        for line in run_command(command):
            string += line
        return string

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
