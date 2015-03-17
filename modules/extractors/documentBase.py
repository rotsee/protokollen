# -*- coding: utf-8 -*-
"""This module contains the base class for all document classes.
"""

from modules.utils import get_date_from_text, get_single_date_from_text


class ExtractionNotAllowed(Exception):
    """The author of this file has disallowed extraction somehow.
    """


class CompatibilityError(Exception):
    """Our libraries and/or helper programmes could not understand this file.
       The file might be malformed.
    """


class DocumentType(object):
    """Store document types.
    """
    UNKNOWN = 0
    MEETING_MINUTES = 1
    AGENDA = 2
    ATTACHMENT = 3


class Page(object):
    """Base class for page classes for various document types.
       Used in extractor classes.
    """

    page_number = None
    """Starting with 1, this is the position of this Page object
       within a file. This is not necessarily the same thing as
       the page number within the original document, as one file
       can contain multiple documents, and page breaks can sometimes
       be put in different places by different renderers (in the
       case of .doc files, etc.)
    """

    def __init__(self):
        pass

    def get_text(self):
        """Should return all plain text in this page.

           Consider caching the result.
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_header(self):
        """Should return a best guess for the header (if any) of this page,
           or None if no headers were found.
        """
        return None

    def get_date(self):
        """Returns a datetime date from the page header.
        """
        return get_single_date_from_text(self.get_header())

    def word_count(self):
        """Returns the number of non whitespace characters.

           Used to find out if OCR is needed
        """
        import re
        char_list = re.findall("(\S+)", self.get_text())
        return len(char_list)


class ExtractorBase(object):
    """Base class for extractor classes for various document types.
       Contains some common functionality, and definitions of
       mandatory methods for sub classes.
    """

    def __init__(self, path):
        self.path = path
        self.text = None

    def get_metadata(self):
        """Should return a metadata.Metadata object
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_text(self):
        """Should return all text content from the document as plain text.
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_header(self):
        """Should return the generic page header content for pages in
           this document. Prefer Page.get_header if available.
        """
        return ""

    def get_next_page(self):
        """Should yield a Page object
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_date(self):
        """Return a best guess for the date of the meeting
           this document refers to, based on the whole text.

           Used as a fallback when Page.get_date does not return a
           page specific date.

           Do NOT rely on metadata to get the date, as that will
           more often than not be wrong.
        """
        date = None

        header_text = self.get_header()
        date = get_single_date_from_text(header_text)

        if date is None:
            text = self.get_text()
            date = get_date_from_text(text)
        return date

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
