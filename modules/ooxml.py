#coding=utf-8
"""This module includes tools for handling and extracting text from
    Office Open XML and modern Mocrosoft Word (.docx) files.
"""

from documentBase import ExtractorBase

from docx import opendocx, getdocumenttext #good for text, bad for metadata
import openxmllib #good for metadata, bad for text
from modules.metadata import Metadata

class DocxExtractor(ExtractorBase):
    """Class for getting plain text from a Office Open XML file.
    """

    def get_metadata(self):
        """Returns a .modules.metadata.Metadata object
        """
        metadata = Metadata()
        document = openxmllib.openXmlDocument(path=self.path)
        metadata.add(document.allProperties, "ooxml")
        return metadata

    def get_text(self):
    	"""Returns all text content from the document as plain text.
        """
        document = opendocx(self.path)
        paratextlist = getdocumenttext(document)
        return "\n".join(paratextlist)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()
