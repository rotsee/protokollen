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
    """Class containing PDF pages extracted with PdfMinerWrapper.
    """

    def __init__(self, LTPage, page_number):
        self.LTPage = LTPage
        self.page_number = page_number

    def get_text(self):
        """Iterate through the list of LT* objects and capture all text.

           Text is cached on first call.
        """
        try:
            return self._text_cache
        except AttributeError:  # cache is not there
            pass

        text_content = []
        for lt_obj in self.LTPage:
            text_content.append(self._parse_obj(lt_obj))
        self._text_cache = '\n'.join(text_content)

        return self._text_cache

    def get_header(self):
        """Tries to guess what text belongs to the page header.

           FIXME We should check actual coordinates for each object, to find
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


class PdfPageFromOcr(PdfPage):
    """Represents a OCR:ed page from a PDF file
    """
    def __init__(self, path, page_number):
        self.pdf_path = path
        self.page_number = page_number
        self._text_cache = self.do_ocr()

    def get_header(self):
        rows = self.get_text().split("\n")
        i = 0
        header_text = []
        for row in rows:
            text_length = len(row.strip())
            # Break on first paragraph
            if text_length > 100:
                break
            # or break on 5th object with content.
            # Only text here, hence lower limit than in parent method
            elif i > 4:
                break
            else:
                header_text.append(row)
            if text_length > 0:
                i += 1
        return '\n'.join(header_text)

    def do_ocr(self):
        import subprocess
        import os
        temp_filename = os.path.join("temp", "ocr.png")
        try:
            arglist = ["gs",
                       "-dSAFE",
                       "-dQUIET",
                       "-o" + temp_filename,
                       "-sDEVICE=png16m",
                       "-r300",
                       "-dFirstPage=" + str(self.page_number),
                       "-dLastPage=" + str(self.page_number),
                       self.pdf_path]
            subprocess.call(args=arglist, stderr=subprocess.STDOUT)
        except OSError as e:
            logging.error("Failed to run GhostScript.\
                           I/O error({0}): {1}".format(e.errno, e.strerror))
        #Do OCR
        import time
        time.sleep(1)  # make sure the server has time to write the files
        import Image
        import pytesseract
        text = pytesseract.image_to_string(
            Image.open(temp_filename),
            lang="swe")
        os.unlink(temp_filename)
        return text


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

        page_number = 0
        for page in PDFPage.create_pages(self.document):
            page_number += 1
            interpreter.process_page(page)
            layout = device.get_result()
            yield PdfPage(layout, page_number)

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
                catalog = pdf_miner.document.catalog['Metadata']
                xmp_metadata = resolve1(catalog).get_data()
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
        """Returns the next Page object, representing a page in the PDF
           Will do OCR if needed.
        """
        try:
            for page in self._page_cache:
                yield page
        except AttributeError:  # not cached
            pass

        self._page_cache = []
        with PdfMinerWrapper(self.path) as document:
            for page in document:
                if page.word_count() == 0:
                    logging.info("No text, doing OCR. This will take a while.")
                    ocr_page = PdfPageFromOcr(self.path, page.page_number)
                    self._page_cache.append(ocr_page)
                    yield ocr_page
                else:
                    self._page_cache.append(page)
                    yield page

    def get_text(self):
        """Returns all text content from the PDF as plain text.
        """
        try:
            return self._text_cache
        except AttributeError:  # not cached
            pass

        text_list = []
        for page in self.get_next_page():
            text = page.get_text()
            if text.strip() != "":
                text_list.append(text)
        self._text_cache = '\n'.join(text_list)
        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
