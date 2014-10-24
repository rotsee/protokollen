#coding=utf-8
"""This module contains the base class for all document classes.
"""

class ExtractorBase(object):
    """Base class extractor classes for various document types.
       Contains some common functionality.
       Each child class shoule be able to return the plain text
       from the while file, as well as the header text, if 
       a page header is found.
    """

    def __init__(self, path):
        self.path = path

    def get_metadata(self):
        """Should return a metadata.Metadata object
        """
        raise NotImplementedError('must be overridden by child classes')

    def get_text(self):
    	"""Should returns all text content from the document as plain text.
        """
        raise NotImplementedError('must be overridden by child classes')

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()
