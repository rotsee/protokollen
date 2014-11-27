#coding=utf-8
"""This module includes tools for handling and extracting text from
   HTML files
"""

from modules.extractors.documentBase import ExtractorBase, Page
from modules.metadata import Metadata

from bs4 import BeautifulSoup
from html2text import html2text
from lxml import html as ehtml


class HtmlPage(Page):

    def __init__(self):
        pass

    def get_text(self):
        """Return the whole document as one page. All examples we found have
           in the wild so far, uses one html document per paragraph.
        """
        return self._text

    def get_header(self):
        """Handled at document level (HtmlExtractor)
        """
        return None

    def get_date(self):
        """Handled at document level (HtmlExtractor)
        """
        return None


class HtmlExtractor(ExtractorBase):
    """Class for handling HTML file data extraction.
    """

    def __init__(self, path, **kwargs):
        self.path = path
        self.content_xpath = kwargs.get('html', '//body')
        self.content_soup = None
        self.content_html = None
        self.soup = None

    def _load_content(self):
        with open(self.path, "rb") as file_:
            self.soup = BeautifulSoup(file_)

        with open(self.path, "rb") as file_:
            html = file_.read()
            html = html.decode('utf-8', 'ignore')
            html = self._get_content_portion(html)
            self.content_html = html
            self.content_soup = BeautifulSoup(html)

    def get_next_page(self):
        """Return the whole document in one page (we have no such
           cases in the wild yet, but one could imagine splitting
           up the document per `article` tag, or similar).
        """
        page = HtmlPage()
        page._text = self.get_text()
        yield page

    def get_header(self):
        """Return a best guess for the header (if any) of this page,
           or None if no headers were found.
        """
        if self.content_soup is None:
            self._load_content

        header_tags = []
        for tag in self.content_soup.descendants:
            #Break on bread text
            if tag.string is not None and len(tag.string) > 70:
                break
            if tag.string is not None and len(tag.string) > 1:
                header_tags.append(tag.string.strip())
            #Break after <h_>-tag
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                break
        return "\n".join(header_tags)

    def _get_content_portion(self, html):
        """Use an xPath expression, `self.html`, to carve out
           the actual content.
        """
        root = ehtml.fromstring(html)
        html_list = root.xpath(self.content_xpath)
        try:
            html_out = html_list[0]
            html = ehtml.tostring(html_out)
        except IndexError:
            raise "Html xPath didn't match anything"
        return html

    def get_text(self):
        """Will return the whole document, or a portion pointed out by
           `self.content_xpath`, as markdown text.
        """
        try:
            return self._text_cache
        except AttributeError:  # not cached
            pass

        if self.content_html is None:
            self._load_content
        self._text_cache = html2text(self.content_html)
        return self._text_cache

    def get_metadata(self):
        """Returns a metadata.Metadata object
        """
        if self.soup is None:
            self._load_content()

        metadata = Metadata()
        try:
            metadata.add({"title": self.soup.title.string})
        except Exception:
            pass
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
