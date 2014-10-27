#coding=utf-8
"""This module includes tools for handling and extracting text from
   RTF files
"""

from documentBase import ExtractorBase
from modules.metadata import Metadata


class RtfExtractor(ExtractorBase):
    """Class for getting plain text from a Microsoft Word file.
    """

    def get_metadata(self):
        """Returns a .modules.metadata.Metadata object
        """
        pass

    def get_text(self):
        """Returns all text content from the document as plain text.
        """
        pass

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
