#coding=utf-8
"""This module includes tools for handling and extracting text from PDF files.
"""

from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

from modules.metadata import Metadata
from pdfminer.pdfparser import PDFParser, PDFDocument
from xmp import xmp_to_dict
from pdfminer.pdftypes import resolve1

class PdfExtractor(object):
    """Class for getting plain text from a PDF file.
    """

    def __init__(self, path):
        self.path = path

    def getMetadata(self):
    	"""Returns metadata from both
    	   the info field (older PDFs) and XMP (newer PDFs).
           Return format is a .modules.metadata.Metadata object
    	"""
        fp = open(self.path, 'rb')
        parser = PDFParser(fp)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize()
        metadata = Metadata()
        for i in doc.info:
        	metadata.add(i)
        if 'Metadata' in doc.catalog:
            xmpMetadata = resolve1(doc.catalog['Metadata']).get_data()
            xmp_dict = xmp_to_dict(xmpMetadata)
            #Let's add only the most useful one
            if "xap" in xmp_dict:
	            metadata.add(xmp_dict["xap"])
            if "pdf" in xmp_dict:
	            metadata.add(xmp_dict["pdf"])
            if "dc" in xmp_dict:
	            metadata.add(xmp_dict["dc"], metadataType="dc")
        fp.close()
        return metadata

    def getText(self):
    	"""Returns all text content from the PDF as plain text.
    	"""
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        laparams.all_texts = True
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        fp = file(self.path, 'rb')
        process_pdf(rsrcmgr, device, fp)
        fp.close()
        device.close()

        str = retstr.getvalue()
        retstr.close()
        return str

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()
