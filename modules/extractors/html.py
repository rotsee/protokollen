#coding=utf-8
"""This module includes tools for handling and extracting text from
   HTML files
"""

from modules.extractors.documentBase import ExtractorBase, Page
from modules.metadata import Metadata

from bs4 import BeautifulSoup
from html2text import html2text


class HtmlPage(Page):

    def __init__(self):
        pass

    def get_text(self):
        """Return the whole document as one page. All examples we found have
           in the wild so far, uses one html document per paragraph.
        """
        return self._text

    def get_header(self):
        """Return a best guess for the header (if any) of this page,
           or None if no headers were found.
        """
        # ta allt som kommer före en tagg med > 100 ch || en <h>
        return None

    def get_date(self):
        #Hur hantera Malmö? Manuellt?
        pass


class HtmlExtractor(ExtractorBase):
    """Class for handling HTML file data extraction.
    """

    def __init__(self, path, **kwargs):
        self.path = path
        self.text = None
        self.content_xpath = kwargs.get('html', None)
        self.soup = BeautifulSoup(open(path))

    def get_next_page(self):
        """Return the whole document in one page (we have no such
           cases in the wild yet, but one could imagine splitting
           up the document per `article` tag, or similar).
        """
        page = HtmlPage()
        page._text = self.get_text()
        yield page

    def get_text(self):
        """Will return the whole document, or a portion pointed out by
           `self.content_xpath`, as markdown text.
        """
        with open(self.path, "rb") as file_:
            html = file_.read()
            html = html.decode('utf-8')
            if self.content_xpath is not None:
                from lxml import html as ehtml
                root = ehtml.fromstring(html)
                html_list = root.xpath(self.content_xpath)
                try:
                    html_out = html_list[0]
                    html = ehtml.tostring(html_out)
                except IndexError:
                    raise "Html xPath didn't match anything"
            return html2text(html)

    def get_metadata(self):
        """Returns a metadata.Metadata object
        """
        metadata = Metadata()
        metadata.add({"title": self.soup.title.string})
        for meta_tag in self.soup.find_all('meta'):
            key = meta_tag.get('name', None) or meta_tag.get('property', None)
            metadata.add({key: meta_tag.get('content')},
                         metadataType="html")
        for link_tag in self.soup.find_all('link'):
            metadata.add({meta_tag.get('rel'): meta_tag.get("href")},
                         metadataType="html")

        return metadata


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
