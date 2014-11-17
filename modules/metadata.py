#coding=utf-8
"""This module contains the Metadata class, for storing metadata from files.
"""
from modules.utils import make_unicode


class Properties():
    """Contains keys and constants for useful metadata properties.
       `dictionary.common` can be overridden by more specific dictionaries,
       see `Creator` vs `mso.Creator`, where Creator has different meanings in
       different contexts.
    """

    SOFTWARE = u"software"
    AUTHOR = u"author"
    TITLE = u"title"
    DESCRIPTION = u"description"
    MODIFICATION_DATE = u"modification_date"
    CREATION_DATE = u"creation_date"
    ORGANISATION = u"organisation"

    dictionary = {
        u"common": {
            u"Producer": SOFTWARE,
            u"Creator": SOFTWARE,
            u"Generator": SOFTWARE,
            u"generator": SOFTWARE,
            u"CreatorTool": SOFTWARE,
            u"Author": AUTHOR,
            u"author": AUTHOR,
            u"manager": AUTHOR,
            u"Company": AUTHOR,
            u"company": AUTHOR,
            u"operator": AUTHOR,
            u"contributor": AUTHOR,
            u"Last Saved by": AUTHOR,
            u"Title": TITLE,
            u"title": TITLE,
            u"publisher": ORGANISATION,
            u"ModDate": MODIFICATION_DATE,
            u"ModifyDate": MODIFICATION_DATE,
            u"LastModified": MODIFICATION_DATE,
            u"Last Modified": MODIFICATION_DATE,
            u"SourceModified": MODIFICATION_DATE,
            u"MetadataDate": MODIFICATION_DATE,
            u"revision-time": CREATION_DATE,
            u"CreationDate": CREATION_DATE,
            u"CreateDate": CREATION_DATE,
            u"Created": CREATION_DATE,
            u"created": CREATION_DATE,
            u"creation-time": CREATION_DATE,
            u"description": DESCRIPTION,
            u"Description": DESCRIPTION,
            u"Subject": DESCRIPTION,
            u"subject": DESCRIPTION,
            u"doccomm": DESCRIPTION,
        },
        u"mso": {
            # Microsoft Office .doc files
            u"Creator": SOFTWARE,  # This seems to be ambigous?
        },
        u"ooxml": {
            #Office Open XML
            u"creator": AUTHOR,
        },
        u"dc": {
            # Dublin Core
            u"creator": AUTHOR,
            u"date": MODIFICATION_DATE,
        },
        u"html": {
            # DC, as used in HTML meta tags
            u"DC.Description": DESCRIPTION,
            u"DC.Date.Published": CREATION_DATE,
            u"DC.Date.Modified": MODIFICATION_DATE,
            u"DC.Date.Created": CREATION_DATE,
            u"DC.Creator": AUTHOR,
            u"DC.Publisher": ORGANISATION,
            u"DC.Title": TITLE,
            # Other occuring meta tags
            u"ms.topics": DESCRIPTION,
            u"companyname": ORGANISATION,
            u"createdby": AUTHOR,
            u"web_author": AUTHOR,
            # og etc
            u"og:title": TITLE,
            u"og:description": DESCRIPTION,
            u"twitter:title": TITLE,
            u"twitter:description": DESCRIPTION
        }
    }


class Metadata(object):
    """This class will store useful metadata from files,
       in a unified format.
    """

    def __init__(self):
        self.data = {}

    def add(self, metadata, metadataType="common"):
        """Adds metadata from a dictionary, limited nesting allowed.
        """
        for (key, value) in metadata.iteritems():
            if metadataType in Properties.dictionary:
                if key in Properties.dictionary[metadataType]:
                    preferredKey = Properties.dictionary[metadataType][key]
                    self._mergeInto(preferredKey, value)
                    continue
            if key in Properties.dictionary[u"common"]:
                preferredKey = Properties.dictionary[u"common"][key]
                self._mergeInto(preferredKey, value)

    def _remove_control_characters(self, s):
        import unicodedata
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    def _mergeInto(self, key, value):
        """Internal method for baking new values into metadata dictionary.
           Typical `value` values, and desired output include:

             * {"A": ["B", "C"]}  =>  B,C
             * [{"A": "B"}]  => B
             * {'x-default': 'B'} => B
             * ["B", "C"] => B,C
             * "B" => B

        """

        foundValue = value
        if isinstance(value, dict):  # if dict: make list
            foundValue = []
            for (k, v) in value.iteritems():
                v = make_unicode(v)
                foundValue.append(v)
        if isinstance(foundValue, list):  # if list: iterate
            for v in foundValue:
                self._mergeInto(key, v)
            return

        if foundValue:  # foundValue can be None
            foundValue = foundValue.strip()  # by now, foundValue is a string
            foundValue = make_unicode(foundValue)
            if len(foundValue) > 0:
                if key in self.data:
                    if foundValue in self.data[key]:
                        return
                    else:
                        self.data[key].append(foundValue)
                else:
                    self.data[key] = [foundValue]

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
