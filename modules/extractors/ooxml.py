#coding=utf-8
"""This module includes tools for handling and extracting text from
    Office Open XML and modern Mocrosoft Word (.docx) files.
"""

from modules.extractors.documentBase import ExtractorBase, Page

from docx import Document
#from docx import opendocx, getdocumenttext  # good for text, bad for metadata
import openxmllib  # good for metadata, bad for text
from modules.metadata import Metadata


class DocxPage(Page):

    def __init__(self):
        pass

    def get_text(self):
        """Returns all the text in one single page.
           We might be able to use e.g. Abiword to calculate
           approximate page breaks.
        """
        return self._text


class DocxExtractor(ExtractorBase):
    """Class for getting plain text from a Office Open XML file.
    """

    def get_metadata(self):
        """Returns a .modules.metadata.Metadata object
        """
        self.metadata = Metadata()
        document = openxmllib.openXmlDocument(path=self.path)
        self.metadata.add(document.allProperties, "ooxml")
        return self.metadata

    def get_header(self):
        """Our docx library has no support for headers yet.
           For now carve out the header ourselves. Ugly, but works.
        """
        headers = []
        document = Document(self.path)
        #Get header (we know were it is)
        import xml.etree.ElementTree as ET
        for rel, val in document._part._rels.iteritems():
            if val.reltype == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header":
                xml = val._target._blob
                root = ET.fromstring(xml)
                namespaces = dict(w="http://schemas.openxmlformats.org/wordprocessingml/2006/main")
                text_element = root.find(".//w:t", namespaces)
                if text_element.text is not None:
                    headers.append(text_element.text)
        return "\n".join(headers)

    def get_next_page(self):
        """Returns all the text in one single page.
           We might be able to use e.g. Abiword to calculate
           approximate page breaks.
        """
        page = DocxPage()
        page._text = self.get_text()
        yield page

    def get_text(self):
        """Returns all text content from the document as plain text.
        """
        try:
            return self._text_cache
        except AttributeError:  # not cached
            pass

        paratextlist = []
        document = Document(self.path)
        for paragraph in document.paragraphs:
            paratextlist.append(paragraph.text)
        self._text_cache = "\n".join(paratextlist)
        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
