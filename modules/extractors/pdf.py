#coding=utf-8
"""This module includes tools for handling and extracting text from PDF files.
"""

import logging

from modules.extractors.documentBase import ExtractorBase, Page
from modules.metadata import Metadata
from modules.xmp import xmp_to_dict

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter

from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdftypes import resolve1


class PdfPage(Page):

    def __init__(self, LTPage):
        self.LTPage = LTPage

    def get_text(self):
        """Iterate through the list of LT* objects and capture all text
        """
        text_content = []
        for lt_obj in self.LTPage:
            text_content.append(self._parse_obj(lt_obj))
        return '\n'.join(text_content)

    def get_header(self):
        """Tries to guess what text belongs to the page header.

           FIXME We should check actual coordinates for each objects, to find
           the topmost ones. This is a quick and dirty implementation.
        """
        i = 0
        header_text = []
        # Objects are ordered top-to-bottom, left-to-right
        for obj in self.LTPage:
            obj_text = self._parse_obj(obj)
            text_length = len(obj_text.strip())
            if text_length > 100:  # break on first paragraph
                break
            elif i > 7:  # or break on 8th object with content
                break
            else:
                header_text.append(obj_text)
            if text_length > 0:
                i += 1
        return '\n'.join(header_text)

    def _parse_obj(self, lt_obj):
        """Capture all text of a LT* object, and its subobjects
        """
        text_content = []
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            text_content.append(lt_obj.get_text())
        elif isinstance(lt_obj, LTImage):
            pass
        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects,
            # so recurse through the children
            for lt_sub_obj in lt_obj:
                text_content.extend(self._parse_obj(lt_sub_obj))
        return '\n'.join(text_content)


class PdfMinerWrapper(object):

    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.file_pointer = open(self.filename, "rb")
        self.parser = PDFParser(self.file_pointer)
        self.document = PDFDocument(self.parser)
        if not self.document.is_extractable:
            raise PDFTextExtractionNotAllowed
        self.parser.set_document(self.document)
        return self

    def _get_next_page(self):
        """Return the next page as a PDFPage object
        """
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.create_pages(self.document):
            interpreter.process_page(page)
            layout = device.get_result()
            yield PdfPage(layout)

    def __iter__(self):
        return iter(self._get_next_page())

    def __exit__(self, _type, value, traceback):
        self.file_pointer.close()


class PdfExtractor(ExtractorBase):
    """Class for getting plain text from a PDF file.
    """

    def get_metadata(self):
        """Returns metadata from both
           the info field (older PDFs) and XMP (newer PDFs).
           Return format is a .modules.metadata.Metadata object
        """
        with PdfMinerWrapper(self.path) as pdf_miner:
            metadata = Metadata()
            for i in pdf_miner.document.info:
                metadata.add(i)
            if 'Metadata' in pdf_miner.document.catalog:
                xmp_metadata = resolve1(pdf_miner.document.catalog['Metadata']).get_data()
                xmp_dict = xmp_to_dict(xmp_metadata)
                #Let's add only the most useful one
                if "xap" in xmp_dict:
                    metadata.add(xmp_dict["xap"])
                if "pdf" in xmp_dict:
                    metadata.add(xmp_dict["pdf"])
                if "dc" in xmp_dict:
                    metadata.add(xmp_dict["dc"], metadataType="dc")

            self.metadata = metadata
            return metadata

    def get_next_page(self):
        with PdfMinerWrapper(self.path) as document:
            for page in document:
                #FIXME add OCR here
                yield page

    def get_text(self):
        """Returns all text content from the PDF as plain text.
        """
        text_list = []
        for page in self.get_next_page():
            text = page.get_text().strip()
            if text != "":
                text_list.append(page.get_text())
        text = '\n'.join(text_list)

        if (text is None) or (text.strip() == ""):
            logging.info("No text found in PDF. Attempting OCR. This will take a while.")
            #FIXME this should go in a separate method
            #First, convert to image
            import subprocess
            import os
            temp_file_names = os.path.join("temp", "page%03d.png")

            try:
                arglist = ["gs",
                           "-dNOPAUSE",
                           "-sOutputFile=" + temp_file_names,
                           "-sDEVICE=png16m",
                           "-r72",
                           self.path]
                subprocess.call(
                    args=arglist,
                    stdout=subprocess.STDOUT,
                    stderr=subprocess.STDOUT)
            except OSError:
                logging.error("Failed to run GhostScript (using `gs`)")
            #Do OCR
            import time
            time.sleep(1)  # make sure the server has time to write the files
            import Image
            import pytesseract
            text = ""
            for file_ in os.listdir("temp"):
                if file_.endswith(".png"):
                    path_to_file = os.join("temp", file_)
                    text += pytesseract.image_to_string(
                        Image.open(path_to_file),
                        lang="swe")
                    os.unlink(path_to_file)
        self.text = text
        return text

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
