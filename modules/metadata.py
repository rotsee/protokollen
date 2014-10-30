#coding=utf-8
"""This module contains the Metadata class, for storing metadata from files.
"""


class Properties():
    """Contains keys and constants for useful metadata properties.
       `dictionary.common` can be overridden by more specific dictionaries,
       see `Creator` vs `mso.Creator`, where Creator has different meanings in
       different contexts.
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
            "Generator": SOFTWARE,
            "generator": SOFTWARE,
            "CreatorTool": SOFTWARE,
            "Author": AUTHOR,
            "author": AUTHOR,
            "manager": AUTHOR,
            "Company": AUTHOR,
            "company": AUTHOR,
            "operator": AUTHOR,
            "contributor": AUTHOR,
            "Last Saved by": AUTHOR,
            "Title": TITLE,
            "title": TITLE,
            "publisher": ORGANISATION,
            "ModDate": MODIFICATION_DATE,
            "ModifyDate": MODIFICATION_DATE,
            "LastModified": MODIFICATION_DATE,
            "Last Modified": MODIFICATION_DATE,
            "SourceModified": MODIFICATION_DATE,
            "MetadataDate": MODIFICATION_DATE,
            "revision-time": CREATION_DATE,
            "CreationDate": CREATION_DATE,
            "CreateDate": CREATION_DATE,
            "Created": CREATION_DATE,
            "created": CREATION_DATE,
            "creation-time": CREATION_DATE,
            "description": DESCRIPTION,
            "Description": DESCRIPTION,
            "Subject": DESCRIPTION,
            "subject": DESCRIPTION,
            "doccomm": DESCRIPTION,
        },
        "mso": {
        #Microsoft Office .doc files
            "Creator": SOFTWARE,  # This seems to be ambigous?
        },
        "ooxml": {
            #Office Open XML
            "creator": AUTHOR,
        },
        "dc": {
        #Dublin Core
            "creator": AUTHOR,
            "date": MODIFICATION_DATE,
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
            if key in Properties.dictionary["common"]:
                preferredKey = Properties.dictionary["common"][key]
                self._mergeInto(preferredKey, value)

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
                foundValue.append(v)
        if isinstance(foundValue, list):  # if list: iterate
            for v in foundValue:
                self._mergeInto(key, v)
            return

        if foundValue:  # foundValue can be None
            foundValue = foundValue.strip()  # by now, foundValue is a string
            if foundValue != "":
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
