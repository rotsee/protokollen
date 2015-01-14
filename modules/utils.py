#coding=utf-8
""" Utility functions to be used in several modules.
"""
import re

datePatterns = [
    '(19|20)\d{2}-\d{1,2}-\d{1,2}',  # 2014-03-24, 2014-3-24
    '(19|20)\d{2}/\d{1,2}/\d{1,2}',  # 2014/03/24 or 2014/3/24
    '\d{1,2}\.\d{1,2}\.(19|20)\d{2}',  # 24.3.2014
    '\d{1,2}\s(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s(19|20)\d{2}',  # 24 mars 2014
    '\d{1,2}\s(jan|feb|mar|apr|jun|jul|aug|sep|okt|nov|dec)\.?\s?(19|20)\d{2}']  # 24 mar 2014, 24 mar. 2014, 24 mar.2014
"""Date patterns for get_first_date_from_text and get_date_from_text
   “Myndigheternas skrivregler” recommends using 2005-05-24 or 24.5.2005
   in document headers.
"""

python_encodings = ["ascii",
                    "cp037",
                    "cp437",
                    "cp500",
                    "cp775",
                    "cp850",
                    "cp857",
                    "cp858",
                    "cp861",
                    "cp863",
                    "cp865",
                    "cp1026",
                    "cp1250",
                    "cp1252",
                    "cp1257",
                    "latin_1",
                    "iso8859_1",
                    "iso8859_4",
                    "iso8859_9",
                    "iso8859_13",
                    "iso8859_14",
                    "iso8859_15",
                    "mac_latin2",
                    "mac_roman"]
"""Subset of standard encodings supported by Python, that sometimes occurs
   in Swedish documents. For use with encoding guessing algorithms, etc.

   Basically any encoding that contains å,ä and ö seem to have been used by
   someone, at some point.
"""


def make_unicode(str_):
    """This method will try to convert any string to a unicode object,
       using whatever encoding works. This is a last resort, when we
       have no ideas about encodings.

       This method is used when storing metadata, that can be heavily
       messed-up as files are abused by ill-behaved software
    """
    output = u""
    if str_ is None:
        return output
    try:
        output = unicode(str_, 'utf-8')
    except TypeError:
        #Already unicode
        output = str_
    except UnicodeDecodeError:
        # At this point we have no idea of knowing what encoding
        # this might be. Let try a few
        for encoding in python_encodings:
            try:
                output = str_.decode(encoding, "ignore")
                break
            except UnicodeDecodeError:
                continue
    #replace useless 0000-char
    output = output.replace(u"\u0000", u"")
    return output


def is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _get_dates_list(text):
    dates = []
    for pattern in datePatterns:
        dates.extend(re.compile(pattern).findall(text))
    return dates


def get_single_date_from_text(text):
    """ Returns the date portion from a short text, that is known to contain
        one and one date. None if the number of matches is not 1
    """

    if text is not None:
        dates = _get_dates_list(text)

        if (len(dates) == 1):
            import dateutil.parser as dateParser
            return dateParser.parse(dates[0], fuzzy=True)
        else:
            return None


def get_date_from_text(text):
    """ Takes a bunch of text, looks for dates and returns the most common one
        and the number of times it occured.
        Intended to be used with document classes to specifiy the date of the
        documents.
    """

    if text is not None:
        dates = _get_dates_list(text)

        if (len(dates) > 0):
            from collections import Counter
            import dateutil.parser as dateParser

            # Count occurences of each date and get the most common one
            c = Counter(dates).most_common(1)[0]
            # Parse the date
            date = dateParser.parse(c[0], fuzzy=True)
        else:
            # Case: no matcing dates found
            date = None

        return date
