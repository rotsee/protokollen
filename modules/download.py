#coding=utf-8
import logging
import os

class FileType:
	UNKNOWN = 0
	PDF     = 1
	DOC     = 2
	DOCX    = 3
	ODT     = 4
	RTF     = 5
	TXT     = 6

	mimeToTypeDict = {
		'application/pdf': FileType.PDF,
		'application/msword': FileType.DOC,
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCX,
		'application/vnd.oasis.opendocument.text': FileType.ODT,
		'text/rtf': FileType.RTF,
		'text/plain': FileType.TXT
	}

class File:
	"""Represents a file downloaded from the web
	"""
	def __init__(self,
		url,
		localFile,
		userAgent = 'Protokollen; ProtoCollection (http://protokollen.net/)'):
			self.localFile = localFile
			self.success   = False
			self.mimeType  = None

			import urllib2
			import magic
			try:
				url = url.encode('utf-8')
				req = urllib2.Request(url)
				req.add_header('User-agent', userAgent)
				f = urllib2.urlopen(req)

				with open(self.localFile, "wb") as localFileHandle:
					localFileHandle.write(f.read())

			except urllib2.HTTPError, e:
				logging.warning("HTTP Error: %s %s" % (e.code, url) )
			except urllib2.URLError, e:
				logging.warning("URL Error: %s %s" % (e.reason, url) )

			if self.exists():
				self.success = True
				magicMime = magic.Magic(mime=True)
				self.mimeType = magicMime.from_file(self.localFile)
			else:
				logging.warning("Failed to download file from %s" % url)


	def exists(self):
		if os.path.isfile(self.localFile):
			return True
		else:
			return False

	def delete(self):
		os.unlink(self.localFile)

	def getFileType(self):
		return FileType.mimeToTypeDict.get(self.mimeType,None)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()