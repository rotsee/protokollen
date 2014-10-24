#coding=utf-8
"""This module contains the base class for all document classes.
"""

from utils import get_date_from_text

class ExtractorBase(object):
    """Base class extractor classes for various document types.
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
    	"""Should returns all text content from the document as plain text.
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_date(self):
        """Should return a best guess for the date of the meeting
           this document refers to. This is normally a found in the 
           header.
 
           utils.get_date_from_text can be used as a fallback method.
 
           Do NOT rely on metadata to get the date, as this is more 
           often than not wrong.
        """
        if self.text is None:
            logging.warning("No text in document when looking for a date")
        else:
            return get_date_from_text(self.text)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()
