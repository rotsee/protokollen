#coding=utf-8
import logging

class CSVFile:
	"""Imports data from a CSV file in a format suitable for the DataSheet class
	"""
	def __init__(self,filename,delimiter=',',quotechar='"'):
		import csv
		self.delimiter = delimiter
		self.quotechar = quotechar
		self.filename  = filename
		self.data  = []
		self.width = 0
		self.indexRow = []

		try:
			with open(self.filename, 'rb') as csvfile:
				reader = csv.reader(csvfile)
				firstRow = True
				indexRow = []
				for row in reader:
					if firstRow:
						self.indexRow = row
						self.width = len(indexRow)
						firstRow = False
					else:
						rowObj = {}
						i = 0
						for col in row:
							if i < self.width:
								colName = self.indexRow[i]
								rowObj[colName] = col or None
							else:
								pass #skip columns outside headers
							i += 1
						self.data.append(rowObj)
		except OSError as err:
			logging.error("OSError in class CSVFile: %s" % err)


class GoogleSheet:
	"""Imports data from a Google Spreadsheet, in a format suitable for the DataSheet class
	"""
	def __init__(self,googleSheetKey):
		import login
		self.key = googleSheetKey
		self.data = []

		#Two step authorization
		from oauth2client.client import SignedJwtAssertionCredentials
		private_key = self._getPrivateKeyFromP12File(login.google_p12_file)
		OAuth2Credentials = SignedJwtAssertionCredentials(
			login.google_client_email,
			private_key,
			'https://spreadsheets.google.com/feeds')
		import gdata.gauth
		import gdata.spreadsheets.client
		OAuth2Token = gdata.gauth.OAuth2TokenFromCredentials(OAuth2Credentials)
		gd_client = gdata.spreadsheets.client.SpreadsheetsClient()
		OAuth2Token.authorize(gd_client)
		gd_client.debug = True

		listFeed = gd_client.GetListFeed(googleSheetKey,1)
		for i, entry in enumerate(listFeed.entry):
			self.data.append(entry.to_dict())

	def _getPrivateKeyFromP12File(self,filename):
		f = file(filename, 'rb')
		private_key = f.read()
		f.close()
		return private_key


class DataSet:
	"""Represents a tabular data set, from a CSV file or similar.
	   data is supposed to be a list of dictionaries
	   [{A: a1, B: b1}, {A: a2, B: b2}, ...]
	"""

	def __init__(self,data):
		self.data = data

	def getNext(self):
		for row in self.data:
			yield row
