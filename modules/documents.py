# -*- coding: utf-8 -*-
"""This module contains classes for documents, and lists of documents.
   Documents are defined by the document rules in settings.py

   A file can contain one or more document. However, a document can
   not be constructed from more than one file. This is a limitation,
   obvious in cases like Gotlands kommun, where meeting minutes are
   split up in a large number of files.
"""

import settings
from modules.utils import make_unicode, last_index
from modules.extractors.documentBase import ExtractionNotAllowed


class DocumentList(object):
    """Contains a list of documents, extracted from a file.
    """

    def __init__(self, extractor):
        """Create a list of documents, using `extractor`
        """

        self._documents = []

        page_types_and_dates = []
        """Keep track of documents by type and date, to be able to merge
           documents depending on `settings.document_type_settings`
        """

        # Loop through pages, and add pages of the same type and date together
        last_page_type = None
        last_page_date = None
        documents = []
        try:
            for page in extractor.get_next_page():
                temp_doc = Document(page, extractor)

                if (len(documents) > 0 and
                   temp_doc.type_ == last_page_type and
                   temp_doc.date == last_page_date):
                    documents[-1].merge_with(temp_doc)
                else:
                    documents.append(temp_doc)
                    page_types_and_dates.append((temp_doc.type_, temp_doc.date))

                last_page_type = temp_doc.type_
                last_page_date = temp_doc.date
        except ExtractionNotAllowed:
            raise ExtractionNotAllowed

        # merge documents, if disallow_infixes == True
        doc_settings = settings.document_type_settings
        disallow_infixes = [d for d in doc_settings
                            if doc_settings[d]["disallow_infixes"] is True]
        """Document types that disallow holes"""

        num_docs = len(page_types_and_dates)
        i = 0
        while i < num_docs:
            (type_, date) = page_types_and_dates[i]
            last_match = last_index(page_types_and_dates, (type_, date))
            if type_ in disallow_infixes and last_match > i:
                num_docs_to_merge = last_match - i + 1
                new_doc = documents.pop(0)
                for j in range(i, last_match):
                    new_doc.merge_with(documents.pop(0))
                self._documents.append(new_doc)
                i += num_docs_to_merge
            else:
                doc_to_merge = documents.pop(0)
                self._documents.append(doc_to_merge)
                i += 1

    def get_next_document(self):
        for document in self._documents:
            yield document

    def __len__(self):
        """len is the number of documents"""
        return len(self._documents)


class Document(object):
    """Represents a single document
    """
    text = ""
    header = ""
    date = None
    type_ = None

    def __init__(self, page, extractor):
        """Create a document stub from a page. Use add_page
           to keep extending this document.
        """
        self.text = page.get_text()
        self.header = page.get_header() or extractor.get_header()
        self.date = page.get_date() or extractor.get_date()
        self.type_ = self.get_document_type()
        self.date = page.get_date() or extractor.get_date()

    def append_page(self, page):
        """Append content from a page to this document.
        """
        pass

    def append_text(self, text):
        """Append content to this document.
        """
        self.text += text

    def merge_with(self, document):
        """Merge this document with another one"""
        try:
            self.text += document.text
        except UnicodeDecodeError:
            self.text = make_unicode(self.text) + make_unicode(document.text)

    def __len__(self):
        """len is the length of the total plaintext"""
        return len(self.text)

    def get_document_type(self):
        """
         Return the first matching document type, based on this
         header text.
        """
        for document_type in settings.document_rules:
            if self.parse_rules(document_type[1], self.header):
                return document_type[0]
        return None

    def parse_rules(self, tuple_, header):
        """Parse document rules. See settings.py for syntax"""
        rule_key = tuple_[0].upper()
        rule_val = tuple_[1]
        header = header.upper()
        # --------- Logical separators --------
        if rule_key == "AND":
            hit = True
            for rule in rule_val:
                hit = hit and self.parse_rules(rule, header)
            return hit
        elif rule_key == "OR":
            hit = False
            for rule in rule_val:
                hit = hit or self.parse_rules(rule, header)
            return hit
        elif rule_key == "NOT":
            hit = not self.parse_rules(rule_val, header)
            return hit
        # -------------- Rules ----------------
        elif rule_key == "HEADER_CONTAINS":
            try:
                pos = make_unicode(header).find(rule_val.upper())
            except UnicodeDecodeError:
                pos = -1
            return pos > -1

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
