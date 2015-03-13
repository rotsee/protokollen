# -*- coding: utf-8 -*-
""" Utility functions to be used in several modules.
"""
import re

datePatterns = [
    '((19|20)\d{2}-\d{1,2}-\d{1,2})',  # 2014-03-24, 2014-3-24
    '((19|20)\d{2}/\d{1,2}/\d{1,2})',  # 2014/03/24 or 2014/3/24
    '(\d{1,2}\.\d{1,2}\.(19|20)\d{2})',  # 24.3.2014
    '(\d{1,2}\s(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s(19|20)\d{2})',  # 24 mars 2014
    '(\d{1,2}\s(jan|feb|mar|apr|jun|jul|aug|sep|okt|nov|dec)\.?\s?(19|20)\d{2})']  # 24 mar 2014, 24 mar. 2014, 24 mar.2014
"""Date patterns for get_first_date_from_text and get_date_from_text
   “Myndigheternas skrivregler” recommends using 2005-05-24 or 24.5.2005
   in document headers. 24 mars 2014 is also not uncommon.
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


def last_index(list_, value):
    """Return the index of the last occurance if an item in a list, or None
    """
    try:
        return (len(list_) - 1) - list_[::-1].index(value)
    except ValueError:
        return None


def is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def replace_set(text, dictionary):
    import re

    rep = dict((re.escape(k), v) for k, v in dictionary.iteritems())
    pattern = re.compile("|".join(rep.keys()))
    return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)


def _get_dates_list(text):
    dates = []
    for pattern in datePatterns:
        dates.extend(re.compile(pattern).findall(text))
    return dates


def _parse_date(date):
    import dateutil.parser as dateParser
    from datetime import datetime
    month_dict = {u"januari": u"January",
                  u"februari": u"February",
                  u"mars": u"March",
                  u"april": u"April",
                  u"maj": u"May",
                  u"juni": u"June",
                  u"juli": u"July",
                  u"augusti": u"August",
                  u"september": u"September",
                  u"oktober": u"October",
                  u"november": u"November",
                  u"december": u"December",
                  u"okt": u"October"}
    date_string = replace_set(date, month_dict)

    try:
        parsed_date = dateParser.parse(date_string,
                                       fuzzy=True,
                                       ignoretz=True,  # No timezones used
                                       yearfirst=True,  # 2014-03-24
                                       dayfirst=True)  # 24.3.2014
        now = datetime.now()
        if parsed_date > now:
            # Future date, can't be right
            parsed_date = None
    except ValueError:
        parsed_date = None
    return parsed_date


def get_single_date_from_text(text):
    """ Returns the date portion from a short text, that is known to contain
        one and only one date. None if the number of matches is not 1
    """

    if text is not None:
        dates = _get_dates_list(text)

        if (len(dates) == 1):
            return _parse_date(dates[0][0])
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
            # Count occurences of each date and get the most common one
            c = Counter(dates).most_common(1)[0]
            # Parse the date
            return _parse_date(c[0][0])
        else:
            # Case: no matcing dates found
            return None

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
