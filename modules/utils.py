#coding=utf-8

""" Utility functions to be used in several modules.
"""
import re


def get_date_from_text(text):
    """ Takes a bunch of text, looks for dates and returns the most common one
        and the number of times it occured.
        Intended to be used with document classes to specifiy the date of the
        documents.
    """

    # Specify available date formats (regex)
    # This part should probably be improved with more patterns
    # “Myndigheternas skrivregler” recommends using 2005-04-14 or 15.4.2005
    # in document headers
    datePatterns = [
        '\d{4}-\d{1,2}-\d{1,2}',  # 2014-04-24 or 2014-4-24
        '\d{4}/\d{1,2}/\d{1,2}',  # 2014/04/24 or 2014/4/24
        '\d{1,2}\.\d{1,2}\.\d{4}',  # 24.4.2014
    ]

    # Parse the text for these patterns and store matches in a list
    dates = []
    for pattern in datePatterns:
        dates = dates + re.compile(pattern).findall(text)

    if (len(dates) > 0):
        from collections import Counter
        import dateutil.parser as dateParser

        # Count occurences of each date and get the most common one
        c = Counter(dates).most_common(1)[0]
        n = c[1]
        # Parse the date
        date = dateParser.parse(c[0], fuzzy=True)
    else:
        # Case: no matcing dates found
        date = None
        n = 0

    return {"date": date, "n": n}
