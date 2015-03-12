# -*- coding: utf-8 -*-
"""This module includes tools for handling and extracting text from
   RTF files
"""

from modules.extractors.doc import DocExtractor
from modules.metadata import Metadata
import rtf2xml.ParseRtf


class RtfExtractor(DocExtractor):
    """Class for handling RTF file data extraction.

       We will mostly be using the same logic as for MSDoc files, but we need
       another way to extract metadata, as wVSummary doesn't work on RTF
    """

    NS_RTF = "http://rtf2xml.sourceforge.net/"

    def _namespace(self, element):
        import re
        m = re.match('\{.*\}', element.tag)
        return m.group(0) if m else ''

    def _tag_name(self, element):
        import re
        m = re.match('\{.*\}(.*)', element.tag)
        return m.group(1) if m else ''

    def get_metadata(self):
        """Returns a metadata.Metadata object

           See http://www.biblioscape.com/rtf15_spec.htm
           for RTF metadata specification
        """
        import os
        temp_filename = os.path.join("temp", "tmp.rtf.xml")

        parse_obj = rtf2xml.ParseRtf.ParseRtf(in_file=self.path,
                                              out_file=temp_filename)
        parse_obj.parse_rtf()
        metadata = Metadata()

        import xml.etree.ElementTree as ET
        tree = ET.parse(temp_filename)
        root = tree.getroot()
        section = root.find(".//{%s}doc-information" % self.NS_RTF)
        if len(section) > 0:
            for tag in section.iterfind(".//*"):
                tag_name = self._tag_name(tag)
                if tag.text is not None:
                    metadata.add({tag_name: tag.text})
                elif tag.get("year") is not None and tag.get("year") != "0":
                    date_parts = []
                    date_parts.append(tag.get("year"))
                    date_parts.append(tag.get("month").zfill(2) or "01")
                    date_parts.append(tag.get("day").zfill(2) or "01")
                    date_str = "-".join(date_parts)
                    metadata.add({tag_name: date_str})

        os.unlink(temp_filename)
        return metadata


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
