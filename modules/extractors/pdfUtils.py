# -*- coding: utf-8 -*-
"""Various helper methods for PDF extraction.
"""

# This file contains mostly unused leftovers from pdf.py.


class Stream (object):
    """Wrapper around PdfMiner's stream class"""

    def __init__(self, stream):
        self.stream = stream

    def get(self, attribute):
        """Returns a cleaned up PDF stream attribute value
        """
        try:
            value = self.stream[attribute]
            return str(value).strip("/_").lower()
        except Exception:
            return None

"""
from pdfminer.pdftypes import resolve1, PDFObjRef
from binascii import b2a_hex
import zlib
from pdfminer.ccitt import ccittfaxdecode


hexadecimal = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
               '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12,
               'd': 13, 'e': 14, 'f': 15}
base85m4 = long(pow(85, 4))
base85m3 = long(pow(85, 3))
base85m2 = long(pow(85, 2))

def get_colormode(color_space, bits=None):
    color_mode = None
    if isinstance(color_space, list):
        color_space_family = _clean_up_stream_attribute(color_space[0])
    else:
        color_space_family = _clean_up_stream_attribute(color_space)

    if color_space_family == "indexed":
        color_schema = color_space[1]
        if isinstance(color_schema, PDFObjRef):
            color_schema = color_schema.resolve()
        if isinstance(color_schema, list):
            color_schema = color_schema[0]
        color_schema = _clean_up_stream_attribute(color_schema)

        bits = color_space[2] or bits
        if isinstance(bits, PDFObjRef):
            bits = bits.resolve()

        if color_schema == "devicegray" and bits == 1:
            color_mode = "1"
        elif color_schema == "devicegray" and bits == 8:
            color_mode = "L"
        elif color_schema == "iccbased":
            # FIXME This just happens to work often enough. We should
            # let PDFMiner take care of all this work, though, rather
            # than implementníng all the logic (this is complex!) ourselves
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
        color_mode = "L"
    elif color_space_family == "devicegray":
        if bits == 8:
            color_mode = "L"
        else:
            color_mode = "1"
    elif color_space_family == "devicergb":
        color_mode = "RGB"
    elif color_space_family == "devicecmyk":
        pass
    return color_mode


def _clean_up_stream_attribute(self, attribute):
    try:
        return str(attribute).strip("/_").lower()
    except Exception:
        return None

def _decompress(self):
    Decompress the image raw data in this image

    if self._filter == 'asciihexdecode':
        self._raw_data = self._asciihexdecode(self._raw_data)
    elif self._filter == 'ascii85decode':
        self._raw_data = self._ascii85decode(self._raw_data)
    elif self._filter == 'flatedecode':
        self._raw_data = zlib.decompress(self._raw_data)
    elif self._filter == "ccittfaxdecode":
        self._raw_data = ccittfaxdecode(self._raw_data, self._filter_params)
    return None

def _determine_image_type(self, stream_first_4_bytes):
    Find out the image file type based on the magic number

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
     Read the string, converting the pairs of digits to
        characters

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

def _get_image(self):
Return an image from this image data.
    
    temp_image = None
    image_data = self._stream.get_data()
    print "len(image_data)",
    print len(image_data)
    try:
        # Assume war image data
#            temp_image = Image.frombuffer(self.color_mode,
#                                          (self.width, self.height),
#                                          self._raw_data, "raw",
#                                          self.color_mode, 0, 1)
        temp_image = Image.frombuffer(self.color_mode,
                                      (self.width, self.height),
                                      image_data, "raw",
                                      self.color_mode, 0, 1)
    except Exception:
        # Not raw image data.
        # Can we make sense of this stream some other way?
        try:
            import StringIO
#                temp_image = Image.open(StringIO.StringIO(self._raw_data))
            temp_image = Image.open(StringIO.StringIO(image_data))
        except Exception:
            # PIL failed us. Try to print data to a file, and open it
#                file_ext = self._determine_image_type(self._raw_data[0:4])
            file_ext = self._determine_image_type(image_data[0:4])
            if file_ext:
                # TODO use tempfile
                file_name = os_sep.join(["header", file_ext])
                with open("temp/" + file_name, "w") as image_file:
#                        image_file.write(self._raw_data)
                    image_file.write(image_data)
                temp_image = Image.open(image_file)

    return temp_image or None
"""
"""
        if "F" in image_obj.stream:
            self._filter = self._clean_up_stream_attribute(image_obj.stream["F"])
        else:
            self._filter = self._clean_up_stream_attribute(image_obj.stream["Filter"])
        if "DP" in image_obj.stream:
            self._filter_params = image_obj.stream["DP"]
        elif "DecodeParms" in image_obj.stream:
            self._filter_params = image_obj.stream["DecodeParms"]
        elif "FDecodeParms" in image_obj.stream:
            self._filter_params = image_obj.stream["FDecodeParms"]

        self._bits = image_obj.stream["BitsPerComponent"]
        self._raw_data = image_obj.stream.get_rawdata()

        if self._filter is not None:
            self._decompress()
        if "CS" in image_obj.stream:
            self.colorspace = image_obj.stream["CS"]
        elif "ColorSpace" in image_obj.stream:
            self.colorspace = image_obj.stream["ColorSpace"]
        else:
            self.colorspace = "DeviceGray"

        if isinstance(self.colorspace, PDFObjRef):
            self.colorspace = self.colorspace.resolve()
        self.color_mode = self.get_colormode(self.colorspace,
                                             bits=self._bits)
        if self.color_mode is None:
            print self.colorspace
            raise Exception("No method for handling colorspace")
"""
