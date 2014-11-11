#coding=utf-8
"""This module includes tools for handling and extracting text from
   HTML files
"""

from modules.extractors.documentBase import ExtractorBase, Page
from modules.metadata import Metadata


class HtmlPage(Page):

    def __init__(self):
        pass

    def get_text(self):
        """An HTML page is treater as one, single, long page,
           at least for now
        """
        return self._text


class HtmlExtractor(ExtractorBase):
    """Class for handling HTML file data extraction.
    """

    def __init__(self, path, **kwargs):
        self.path = path
        self.text = None
        self.content_xpath = kwargs.get('html', None)

    def get_next_page(self):
        page = HtmlPage()
        page._text = self.get_text()
        yield page

    def get_text(self):
        return None

    def get_metadata(self):
        """Returns a metadata.Metadata object
        """
        return Metadata()


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
