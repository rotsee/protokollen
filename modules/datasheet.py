#coding=utf-8

import logging


class Row(dict):
    """Represents a row in a datasheet
    """

    def __init__(self, *arg, **kw):
        super(Row, self).__init__(*arg, **kw)

    def enumerated_columns(self, enumerated_header):
        """Return a list of column values corresponding
           to an enumerated header.
        """
        columns = []
        for header in enumerated_header:
            columns.append(self.get(header, None))
        return columns

    def list(self):
        """Return a list of column values, sorted by key.
           Useful for headerless datasets. """
        columns = []
        for key in sorted(self):
            columns.append(self[key])
        return columns


class DataSet(object):
    """Represents a tabular data set, from a CSV file or similar.
       Inputed data is supposed to be a list of dictionaries or Row objects:
       [{A: a1, B: b1}, {A: a2, B: b2}, ...]
    """

    def __init__(self, data):
        self.data = []
        self.headers = []
        for row in data:
            self.data.append(Row(row))
            self._append_keys_to_header(row)

    def _append_keys_to_header(self, dictionary):
        for key in dictionary.keys():
            if not key in self.headers:
                self.headers.append(key)

    def get_enumerated_headers(self, name, start_from=1):
        """Returns a list of headers (keys) on the form
           [name1, name2, name3]
        """
        header_list = []
        i = start_from
        while name + str(i) in self.headers:
            header_list.append(name + str(i))
            i += 1
        return header_list

    def get_length(self):
        """Total number of rows in DataSet
        """
        return len(self.data)

    def filter(self, require=None, disallow=None):
        """Filter out rows, depending on requires and/or disallowed keys.
           `require` and `disallow` are lists of keys.
        """
        filtered_list = []
        for row in self.data:
            ok = True
            for r in require or []:
                if r in row and row[r] is not None:
                    pass
                else:
                    ok = False
            for d in disallow or []:
                if d in row and row[d] is not None:
                    ok = False
                    break
            if ok:
                filtered_list.append(row)
        self.data = filtered_list

    def shuffle(self):
        """Randomly (kind of) reorder the rows
        """
        from random import shuffle
        shuffle(self.data)

    def get_next(self):
        """Get the rows, one at a time:

              for row in my_data.getNext():
                  print row
        """
        for row in self.data:
            yield row


class HeaderlessDataSet(DataSet):
    """Represents a tabular data set, where the data does not have column
       headers. Inputed data is supposed to be a list of lists:
       [[a, b, c], [aa, bb, cc]], ...].
    """

    def __init__(self, data):
        self.data = []
        self.headers = None
        self.width = 0

        for row in data:
            self.width = max(self.width, len(row))
            i = 0
            data_row = {}
            for col in row:
                data_row[str(i)] = col
                i += 1
            self.data.append(Row(data_row))


class CSVFile(DataSet):
    """Represents data from a CSV file. Data is loaded on init.
    """
    def __init__(self, filename,
                 delimiter=',', quotechar='"', has_headers=True):
        import csv
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.filename = filename
        self.data = []
        self.width = 0
        self.headers = []

        try:
            with open(self.filename, 'rb') as csvfile:
                reader = csv.reader(csvfile)
                firstRow = has_headers
                for row in reader:
                    if firstRow:
                        self.headers = row
                        self.width = len(self.headers)
                        firstRow = False
                    else:
                        row_dict = {}
                        i = 0
                        if not has_headers:
                            self.width = max(self.width, len(row))
                        for col in row:
                            if i < self.width:
                                if has_headers:
                                    col_name = self.headers[i]
                                else:
                                    col_name = str(i)
                                row_dict[col_name] = col or None
                            else:
                                pass  # skip columns outside headers
                            i += 1
                        self.data.append(Row(row_dict))
        except OSError as err:
            logging.error("OSError in class CSVFile: %s" % err)


class GoogleSheet(DataSet):
    """Represents data from a Google Spreadsheet. Data is loaded on init.
       First row is assumed to contain headers.
    """
    def __init__(self,
                 googleSheetKey,
                 client_email,
                 p12file="google_api.p12",
                 sheet=1):
        self.key = googleSheetKey
        self.data = []
        self.headers = []

        #Two step authorization
        from oauth2client.client import SignedJwtAssertionCredentials
        private_key = self._getPrivateKeyFromP12File(p12file)
        OAuth2Credentials = SignedJwtAssertionCredentials(
            client_email,
            private_key,
            'https://spreadsheets.google.com/feeds')
        import gdata.gauth
        import gdata.spreadsheets.client
        OAuth2Token = gdata.gauth.OAuth2TokenFromCredentials(OAuth2Credentials)
        gd_client = gdata.spreadsheets.client.SpreadsheetsClient()
        gd_client.debug = True
        gd_client.ssl = False
        OAuth2Token.authorize(gd_client)

        ssfeed = gd_client.GetSpreadsheets()
        wsfeed = gd_client.GetWorksheets(self.key)
        #If given a sheet name, rather then a number, look up corresponding id
        if not self.is_number(sheet):
            sheetIDs = self._worksheet_ids(wsfeed)
            if sheet in sheetIDs:
                self.sheet = sheetIDs[sheet]
            else:
                self.sheet = 1
        else:
            self.sheet = sheet

        listFeed = gd_client.GetListFeed(self.key, self.sheet)
        for i, entry in enumerate(listFeed.entry):
            row_dictionary = entry.to_dict()
            self.data.append(Row(row_dictionary))
            self._append_keys_to_header(row_dictionary)

    def _getPrivateKeyFromP12File(self, filename):
        f = file(filename, 'rb')
        private_key = f.read()
        f.close()
        return private_key

    def _worksheet_ids(self, feed):
        import urlparse
        import os

        def _id(entry):
            split = urlparse.urlsplit(entry.id.text)
            return os.path.basename(split.path)
        return dict([
            (entry.title.text, _id(entry))
            for entry in feed.entry
        ])

    def is_number(self, string):
        """Check if input is a number"""
        try:
            float(string)
            return True
        except ValueError:
            return False

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
