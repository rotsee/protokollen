#coding=utf-8
"""This module contains the Metadata class, for storing metadata from files.
"""

class Properties():
    """Contains keys and constants for useful metadata properties from various standards.
       `dictionary.common` can be overridden by more specific dictionaries, 
       see `Creator` vs `dc.creator`, or `date` with potentially different meanings.
    """

    SOFTWARE = "software"
    AUTHOR = "author"
    TITLE = "title"
    DESCRIPTION = "description"
    MODIFICATION_DATE = "modification_date"
    CREATION_DATE = "creation_date"
    ORGANISATION = "organisation"

    dictionary = {
        "common": {
            "Producer": SOFTWARE,
            "Creator": SOFTWARE,
            "CreatorTool": SOFTWARE,
            "Author": AUTHOR,
            "contributor": AUTHOR,
            "Title": TITLE,
            "title": TITLE,
            "publisher": ORGANISATION,
            "ModDate": MODIFICATION_DATE,
            "ModifyDate": MODIFICATION_DATE,
            "LastModified": MODIFICATION_DATE,
            "SourceModified": MODIFICATION_DATE,
            "MetadataDate": MODIFICATION_DATE,
            "CreationDate": CREATION_DATE,
            "CreateDate": CREATION_DATE,
            "description": DESCRIPTION,
            "Subject": DESCRIPTION
        },
        "dc": {
            "creator": AUTHOR,
            "date": MODIFICATION_DATE,
        }
    }

class Metadata(object):
    """This class will store useful metadata from files,
       in a unified format.
    """

    PROPERTIES = {
        ""
    }

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
            if key in Properties.dictionary["common"]:
                preferredKey = Properties.dictionary["common"][key]
                self._mergeInto(preferredKey, value)

    def _mergeInto(self, key, value):
        """Internal method for baking new values into metadata dictionary.
           Typical inputs and desired output include:

             * {"A": ["B", "C"]}  =>  B,C
             * [{"A": "B"}]  => B
             * {'x-default': 'B'} => B
             * ["B", "C"] => B,C
             * "B" => B

        """
        foundValue = value
        if isinstance(value, dict): #if dict: make list
            foundValue = []
            for (k,v) in value.iteritems():
                foundValue.append(v)
        if isinstance(foundValue, list): #if list: iterate
            for v in foundValue:
                self._mergeInto(key, v)
            return

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
