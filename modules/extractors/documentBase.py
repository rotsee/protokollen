#coding=utf-8
"""This module contains the base class for all document classes.
"""

from modules.utils import get_date_from_text
import logging


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

    def __init__(self):
        pass

    def get_text(self):
        """Should return all plain text in this page.
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_date(self):
        """Return a best guess for the date these minutes were taken,
           typically by looking in the page header. Do NOT rely on
           document metadata!

           Returns a datetime object
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_type(self):
        """Return a best guess for the type of document this page belongs to.
           This should be done on page level, as one file can contain multiple
           documents (e.g. meeting minutes, attachments and invitation).

           Returns a DocumentType, e.g. DocumentType.MEETING_MINUTES
        """
        raise NotImplementedError('must be overridden by child classes')


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

    def get_next_page(self):
        """Should yield a Page object
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_date(self):
        """Return a best guess for the date of the meeting
           this document refers to, based on the whole text.

           Used a fallback when Page.get_date does not return a
           page specific date.

           Do NOT rely on metadata to get the date, as this is more
           often than not wrong.
        """
        text = self.get_text()
        if text is None or text == "":
            logging.warning("No text in document when looking for a date")
        else:
            return get_date_from_text(text)

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
