# -*- coding: utf-8 -*-
"""This module includes tools for handling and extracting text from PDF files.
   TODO: Use ui object for user interaction
"""

import logging

from modules.extractors.documentBase import ExtractorBase, Page
from modules.metadata import Metadata
from modules.xmp import xmp_to_dict
from modules.utils import make_unicode

from binascii import b2a_hex
import zlib
from PIL import Image
from os import sep as os_sep
from tempfile import NamedTemporaryFile

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter

from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdftypes import resolve1

hexadecimal = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
               '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12,
               'd': 13, 'e': 14, 'f': 15}
base85m4 = long(pow(85, 4))
base85m3 = long(pow(85, 3))
base85m2 = long(pow(85, 2))


class PDFError(Exception):
    pass


class PdfImage(object):
    """Class representing an image in a PDF.
       Contains methods for extracting images.
    """

    def __init__(self, image_obj):
        """Represents a PDFMiner LTImage object.
           Extracts the actual image data.
        """
        if image_obj.stream is None:
            raise Exception("No image stream")
        if self._clean_up_stream_attribute(image_obj.stream["Subtype"]) != "image":
            raise Exception("Not an image")

        self.width = image_obj.stream["Width"]
        self.height = image_obj.stream["Height"]
        self._filter = self._clean_up_stream_attribute(image_obj.stream["Filter"])
        self._bits = image_obj.stream["BitsPerComponent"]
        self._raw_data = image_obj.stream.get_rawdata()
        if self._filter is not None:
            self._decompress()
        self.color_mode = self.get_colormode(image_obj.stream["ColorSpace"],
                                             bits=self._bits)
        if self.color_mode is None:
            raise Exception("No method for handling colorspace")

    def get_text(self):
        """Does OCR on this image.
        """
        # Some images are flipped. I have no idea how to detect this
        # with PDF Minder, so for now, also OCR the flipped image
        temp_image = self._get_image()
        if temp_image is not None:
            import pytesseract
            text = pytesseract.image_to_string(temp_image, lang="swe")
            text += " \n"
            rotated_image = temp_image.transpose(Image.FLIP_TOP_BOTTOM)
            text += pytesseract.image_to_string(rotated_image, lang="swe")
            #print text
            return text

    def _get_image(self):
        """Return an image from this image data.
        """
        temp_image = None
        try:
            # Assume war image data
            temp_image = Image.frombuffer(self.color_mode,
                                          (self.width, self.height),
                                          self._raw_data, "raw")
        except Exception:
            # Not raw image data.
            # Can we make sense of this stream some other way?
            import StringIO
            temp_image = Image.open(StringIO.StringIO(self._raw_data))
        except Exception:
            # PIL failed us. Try to print data to a file, and open it
            file_ext = self._determine_image_type(self._raw_data[0:4])
            if file_ext:
                # TODO use tempfile
                file_name = os_sep.join(["header", file_ext])
                with open("temp/" + file_name, "w") as image_file:
                    image_file.write(self._raw_data)
                temp_image = Image.open(image_file)

        return temp_image

    def get_colormode(self, color_space, bits=None):
        color_mode = None
        try:
            color_space_family = self._clean_up_stream_attribute(color_space[0])
        except TypeError:
            color_space_family = self._clean_up_stream_attribute(color_space)

        if color_space_family == "indexed":
            color_schema = self._clean_up_stream_attribute(color_space[1])
            bits = color_space[2] or bits
            if color_schema == "devicegray" and bits == 1:
                color_mode = "1"
            elif color_schema == "devicegray" and bits == 8:
                color_mode = "L"
        elif color_space_family == "pattern":
            pass
        elif color_space_family == "separation":
            pass
        elif color_space_family == "devicen":
            pass
        elif color_space_family == "calgray":
            pass
        elif color_space_family == "calrgb":
            pass
        elif color_space_family == "lab":
            pass
        elif color_space_family == "iccbased":
            pass
        elif color_space_family == "devicegray":
            if bits == 8:
                color_mode = "L"
            else:
                color_mode = "1"
        elif color_space_family == "devicergb":
            pass
        elif color_space_family == "devicecmyk":
            pass
        return color_mode

    def _decompress(self):
        """Decompress the image raw data in this image
        """
        if self._filter == 'asciihexdecode':
            self._raw_data = self._asciihexdecode(self._raw_data)
        elif self._filter == 'ascii85decode':
            self._raw_data = self._ascii85decode(self._raw_data)
        elif self._filter == 'flatedecode':
            self._raw_data = zlib.decompress(self._raw_data)
        return

    def _clean_up_stream_attribute(self, attribute):
        try:
            return str(attribute).strip("/_").lower()
        except Exception:
            return None

    def _determine_image_type(self, stream_first_4_bytes):
        """Find out the image file type based on the magic number"""
        file_type = None
        bytes_as_hex = b2a_hex(stream_first_4_bytes)
        if bytes_as_hex.startswith('ffd8'):
            file_type = 'jpeg'
        elif bytes_as_hex == '89504e47':
            file_type = 'png'
        elif bytes_as_hex == '47494638':
            file_type = 'gif'
        elif bytes_as_hex.startswith('424d'):
            file_type = 'bmp'
        return file_type

    def _clean_hexadecimal(self, a):
        """ Read the string, converting the pairs of digits to
            characters
        """
        b = ''
        shift = 4
        value = 0

        try:
            for i in a:
                value = value | (hexadecimal[i] << shift)
                shift = 4 - shift
                if shift == 4:
                    b = b + chr(value)
                    value = 0
        except ValueError:
            raise PDFError("Problem with hexadecimal string %s" % a)
        return b

    def _asciihexdecode(self, text):
        at = text.find('>')
        return self._clean_hexadecimal(text[:at].lower())

    def _ascii85decode(self, text):
        end = text.find('~>')
        new = []
        i = 0
        ch = 0
        value = 0
        while i < end:
            if text[i] == 'z':
                if ch != 0:
                    raise PDFError('Badly encoded ASCII85 format.')
                new.append('\000\000\000\000')
                ch = 0
                value = 0
            else:
                v = ord(text[i])
                if v >= 33 and v <= 117:
                    if ch == 0:
                        value = ((v - 33) * base85m4)
                    elif ch == 1:
                        value = value + ((v - 33) * base85m3)
                    elif ch == 2:
                        value = value + ((v - 33) * base85m2)
                    elif ch == 3:
                        value = value + ((v - 33) * 85)
                    elif ch == 4:
                        value = value + (v - 33)
                        c1 = int(value >> 24)
                        c2 = int((value >> 16) & 255)
                        c3 = int((value >> 8) & 255)
                        c4 = int(value & 255)
                        new.append(chr(c1) + chr(c2) + chr(c3) + chr(c4))
                    ch = (ch + 1) % 5
            i = i + 1
        if ch != 0:
            c = chr(value >> 24) + chr((value >> 16) & 255) + \
                chr((value >> 8) & 255) + chr(value & 255)
            new.append(c[:ch - 1])
        return "".join(new)


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

           FIXME We should check actual coordinates for each object, to find
           the topmost ones. This is a quick and dirty implementation.
        """
        try:
            return self._header_cache
        except AttributeError:  # cache is not there
            pass

        i = 0
        header_text = []
        # Objects are ordered top-to-bottom, left-to-right
        for obj in self.LTPage:
            obj_text = self._parse_obj(obj, do_ocr=True)
            text_length = len(obj_text.strip())
            if text_length > 100:  # break on first paragraph
                break
            elif i > 7:  # or break on 8th object with content
                break
            else:
                header_text.append(obj_text)
            if text_length > 0:
                i += 1

        try:
            self._header_cache = u'\n'.join(header_text)
        except UnicodeDecodeError:
            self._header_cache = u'\n'.join(make_unicode(x) for x in header_text)

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
                text_content.extend(sub_text_content)
        elif (isinstance(lt_obj, LTImage)) and (do_ocr is True):
            # An image
            image = PdfImage(lt_obj)
            text_content.append(image.get_text())

        return ''.join(text_content)


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
        #import Image
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
        try:
            self._text_cache = u'\n'.join(text_list)
        except UnicodeDecodeError:
            self._text_cache = u'\n'.join(make_unicode(x) for x in text_list)

        return self._text_cache

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
