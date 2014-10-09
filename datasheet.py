#coding=utf-8
import logging

class CSVFile:
	"""Imports data from a CSV file in a format suitable for Class DataSheet
	"""
	def __init__(self,filename,delimiter=',',quotechar='"'):
		import csv
		self.delimiter=','
		self.quotechar='"'
		self.filename = filename
		self.data = []
		self.length = 0

		try:
			with open(self.filename, 'rb') as csvfile:
				reader = csv.reader(csvfile)
				for row in reader:
					self.data.append(row)
				self.length = len(self.data)
		except OSError as err:
			logging.error("OSError in class CSVFile: %s" % err)

class DataSet:
	"""Represents a tabular data set, from a CSV file or similar.
	   Inputted data is assumed to have a header, and look like this:
	   [[h1, h2],[r1c1, r1c2],[r2c1,r2c2],...]
	"""

	def __init__(self,data):
		self.indexRow = []
		self.data = []

		firstRow = True
		for row in data:
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

	def getNext(self):
		for row in self.data:
			yield row
