# -*- coding: utf-8 -*-
"""This module includes tools for handling and extracting text from
   old Microsoft Word (.doc) files. It uses the Abiword
"""

from modules.extractors.documentBase import ExtractorBase, Page
from modules.extractors.documentBase import CompatibilityError

import subprocess
from modules.metadata import Metadata


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

    NS_ABW = "http://www.abisource.com/awml.dtd"
    """XML namespace for Abiword documents"""

    def get_metadata(self):
        """Returns a metadata.Metadata object
           Using wVSummary
        """
        command = 'wvSummary ' + self.path
        output = subprocess.check_output(command, shell=True)
        metadata = Metadata()
        for line in output.split("\n"):
            parts = line.strip().replace("\"", "").split(" = ")
            if len(parts) == 2:
                metadata.add({parts[0]: parts[1]}, "mso")
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
        except OSError:
            raise OSError

        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_filename)
        root = tree.getroot()

        text = ""
#        list_ = list(root.iter())
#        for l in list_:
#            print l.tag, l.attrib
#            if not "base64" in l.attrib:
#                print l.text

        section = root.find(".//{%s}section[@type='header']" % self.NS_ABW)
        if section is None:
            # Assuming even and odd headers contain more or less the same data
            section = root.find(".//{%s}section[@type='header-even']" % self.NS_ABW)
        if section is not None:
            for tag in section.iterfind(".//*"):
                if tag.text is not None:
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

        import subprocess
        import os
        temp_filename = os.path.join("temp", "tmp.txt")
        try:
            arglist = ["abiword",
                       self.path,
                       "--to=txt",
                       "--to-name=" + temp_filename
                       ]
            subprocess.call(args=arglist, stderr=subprocess.STDOUT)
        except OSError:
            raise OSError

        self._text_cache = ""
        try:
            with open(temp_filename, 'rb') as file_:
                self._text_cache = file_.read()
        except IOError:
            raise CompatibilityError("Abiword failed to convert this file.")
        os.unlink(temp_filename)
        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
