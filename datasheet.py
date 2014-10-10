#coding=utf-8

class DataSet:
	"""Represents a tabular data set, from a CSV file or similar.
	   data is supposed to be a list of dictionaries
	   [{A: a1, B: b1}, {A: a2, B: b2}, ...]
	"""

	def __init__(self,data):
		self.data = data

	def filter(self,require=None,disallow=None):
		filteredList = []
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
				filteredList.append(row)

		return DataSet(filteredList)

	def shuffle(self):
		from random import shuffle
		shuffle(self.data)

	def getNext(self):
		for row in self.data:
			yield row

class CSVFile(DataSet):
	"""Represents data from a CSV file. Data is loaded on init.
	   First row is assumed to contain headers
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
				for row in reader:
					if firstRow:
						self.indexRow = row
						self.width = len(self.indexRow)
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


class GoogleSheet(DataSet):
	"""Represents data from a Google Spreadsheet. Data is loaded on init.
	   First row is assumed to contain headers.
	"""
	def __init__(self,googleSheetKey,client_email,p12file="google_api.p12"):
		self.key = googleSheetKey
		self.data = []

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