# -*- coding: utf-8 -*-
"""This module includes tools for handling and extracting text from PDF files.
   TODO: Use ui object for user interaction
"""

import logging

from modules.extractors.documentBase import ExtractorBase, Page
from modules.extractors.documentBase import\
    ExtractionNotAllowed, CompatibilityError
from modules.metadata import Metadata
from modules.xmp import xmp_to_dict
from modules.utils import make_unicode
from modules.extractors.pdfUtils import Stream

from PIL import Image
from os import unlink
from os import path as os_path

from pytesseract import image_to_string

from pdfminer.pdfparser import PDFParser, PSEOF, PDFSyntaxError
from pdfminer.pdfdocument import PDFDocument, PDFEncryptionError
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdftypes import resolve1, PDFNotImplementedError
from pdfminer.image import ImageWriter


class PDFError(Exception):
    pass


class PdfImage(object):
    """Class representing an image in a PDF."""

    def __init__(self, image_obj):
        """Takes a PDFMiner LTImage object."""
        if image_obj.stream is None:
            raise Exception("No image stream")

        self.stream = Stream(image_obj.stream)
        if self.stream.get("Subtype") != "image":
            raise Exception("Not an image")

        self._stream = image_obj.stream
        self._image_obj = image_obj

    def get_text(self):
        """Does OCR on this image."""
        image_writer = ImageWriter("temp")
        try:
            temp_image = image_writer.export_image(self._image_obj)
        except PDFNotImplementedError:
            # No filter method available for this stream
            # https://github.com/euske/pdfminer/issues/99
            return u""
        try:
            text = image_to_string(Image.open("temp/" + temp_image),
                                   lang="swe")
        except IOError:
            # PdfMiner did not return an image
            # Let's try to create one ourselves
            # TODO: Create proper color_mode values from ColorSpace
            # Most of the times "L" will create something good enough
            # for OCR, though
            temp_image = Image.frombuffer("L",
                                          self._image_obj.srcsize,
                                          self._stream.get_data(), "raw",
                                          "L", 0, 1)
            text = image_to_string(temp_image, lang="swe")
        unlink("temp/" + temp_image)
        return text


class PdfPage(Page):
    """Class containing PDF pages extracted with PdfMinerWrapper.
    """

    def __init__(self, page_object, page_number):
        self.LTPage = page_object
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
        try:
            self._text_cache = u'\n'.join(text_content)
        except UnicodeDecodeError:
            self._text_cache = u'\n'.join(make_unicode(x) for x in text_content)

        return self._text_cache

    def get_header(self):
        """Tries to guess what text belongs to the page header.
        """
        try:
            return self._header_cache
        except AttributeError:  # cache is not there
            pass

        page_bbox = self.LTPage.bbox
        top_fifth = (page_bbox[3] - page_bbox[0]) * 0.8

        # Get all objects containing text
        all_objects = []
        for obj in self.LTPage:
            obj_text = self._parse_obj(obj, do_ocr=True)
            y1 = obj.bbox[1]
            all_objects.append((y1, obj_text))
        from operator import itemgetter
        all_objects.sort(key=itemgetter(0), reverse=True)

        # Get what looks most like a header
        header_texts = []
        i = 0
        for (y1, obj_text) in all_objects:
            text_length = len(obj_text.strip())
            if text_length > 100:  # break on first paragraph
                break
            elif i > 5:  # or break on 8th object with content
                break
            elif y1 < top_fifth:  # TODO break on 1/5 of page
                break
            else:
                header_texts.append(obj_text)
            if text_length > 0:
                i += 1
        try:
            self._header_cache = u' '.join(header_texts)
        except UnicodeDecodeError:
            self._header_cache = u' '.join(make_unicode(x) for x in header_texts)
        return self._header_cache

    def _parse_obj(self, lt_obj, do_ocr=False):
        """Capture all text of a LT* object, and its subobjects
        """
        text_content = []
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            text_content.append(lt_obj.get_text())
        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects,
            # so recurse through the children
            # lt_obj.matrix
            # TODO apply matrix to images
            for lt_sub_obj in lt_obj:
                sub_text_content = self._parse_obj(lt_sub_obj, do_ocr=do_ocr)
                text_content.append(sub_text_content)
        elif (isinstance(lt_obj, LTImage)) and (do_ocr is True):
            # An image
            try:
                image = PdfImage(lt_obj)
                text_content.append(image.get_text())
            except Exception:
                pass

        try:
            return ''.join(text_content)
        except TypeError:
            # text_content was not a string. Probably a failed image extraction
            return ""


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
            # or break on nth row.
            elif i > 10:
                break
            else:
                header_text.append(row)
            if text_length > 0:
                i += 1
        return '\n'.join(header_text)

    def do_ocr(self):
        import subprocess
        temp_filename = os_path.join("temp", "ocr.png")
        try:
            arglist = ["gs",
                       "-dSAFE",
                       "-dQUIET",
                       "-o" + temp_filename,
                       "-sDEVICE=pnggray",
                       "-r600",
                       "-dFirstPage=" + str(self.page_number),
                       "-dLastPage=" + str(self.page_number),
                       self.pdf_path]
            subprocess.call(args=arglist, stderr=subprocess.STDOUT)
        except OSError as e:
            logging.error("Failed to run GhostScript." +
                          "I/O error({0}): {1}".format(e.errno, e.strerror))
        # Do OCR
        import time
        time.sleep(1)  # make sure the server has time to write the files
        text = image_to_string(
            Image.open(temp_filename),
            lang="swe")
        unlink(temp_filename)
        return text


class PdfMinerWrapper(object):

    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.file_pointer = open(self.filename, "rb")
        try:
            self.parser = PDFParser(self.file_pointer)
            self.document = PDFDocument(self.parser)
        except PSEOF:
            raise CompatibilityError("PdfMiner reported an unexpected EOF")
        except PDFSyntaxError:
            raise CompatibilityError("PdfMiner reported a syntax error")
        except ValueError:
            raise CompatibilityError("PdfMiner could not parse this file")

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
                # Let's add only the most useful one
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
        try:
            with PdfMinerWrapper(self.path) as document:
                for page in document:
                    if page.word_count() == 0:
                        logging.info("No text, doing OCR.")
                        ocr_page = PdfPageFromOcr(self.path, page.page_number)
                        self._page_cache.append(ocr_page)
                        yield ocr_page
                    else:
                        self._page_cache.append(page)
                        yield page
        except PDFTextExtractionNotAllowed:
            # Simply not allowed
            raise ExtractionNotAllowed
        except PDFEncryptionError:
            # I have actually no idea what going on here,
            # but this error occurs in some protected PDF's
            raise ExtractionNotAllowed
        except TypeError:
            raise CompatibilityError

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
        try:
            self._text_cache = u'\n'.join(text_list)
        except UnicodeDecodeError:
            self._text_cache = u'\n'.join(make_unicode(x) for x in text_list)

        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
