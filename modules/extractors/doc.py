#coding=utf-8
"""This module includes tools for handling and extracting text from
   old Microsoft Word (.doc) files. It uses the wv library
"""

from modules.extractors.documentBase import ExtractorBase, Page

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


class DocPage(Page):

    def __init__(self):
        pass

    def get_text(self):
        """Returns all the text in one single page.
           We might be able to use e.g. abiword to calculate
           approximate page breaks.
        """
        return self._text


class DocExtractor(ExtractorBase):
    """Class for getting plain text from a Microsoft Word file.
    """

    NS_ABW = "{http://www.abisource.com/awml.dtd}"
    """XML namespace for Abiword documents"""

    def get_metadata(self):
        """Returns a metadata.Metadata object
        """
        command = 'wvSummary ' + self.path
        metadata = Metadata()
        for line in run_command(command):
            parts = line.strip().replace("\"", "").split(" = ")
            if len(parts) == 2:
                metadata.add({parts[0]: parts[1]}, "mso")
        self.metadata = metadata
        return metadata

    def get_header(self):
        """Uses Abiword to return the first page header encountered.
        """
        import subprocess
        import os
        temp_filename = os.path.join("temp", "tmp.abw")
        try:
            arglist = ["abiword",
                       self.path,
                       "--to=abw",
                       "--to-name=" + temp_filename
                       ]
            subprocess.call(args=arglist, stderr=subprocess.STDOUT)
        except OSError as e:
            pass

        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_filename)
        root = tree.getroot()

        text = ""
        for section in root.find(".//" + self.NS_ABW + "section[@type='header']"):
            for tag in section.iterfind(".//*"):
                if tag.text is not None:
                    print tag.text
                    text += tag.text

        os.unlink(temp_filename)
        return text

    def get_next_page(self):
        """Returns all the text in one single page.
           We might be able to use e.g. Abiword to calculate
           approximate page breaks.
        """
        page = DocPage()
        page._text = self.get_text()
        yield page

    def get_text(self):
        """Returns all text content from the document as plain text.
        """
        try:
            return self._text_cache
        except AttributeError:  # not cached
            pass

        out = ' /dev/stdout'  # ugly, ugly hack. Will only work on *nix
        command = 'wvText ' + self.path + out
        string = ""
        for line in run_command(command):
            string += line
        self._text_cache = string
        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
