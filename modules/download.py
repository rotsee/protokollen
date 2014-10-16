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
		'application/pdf': PDF,
		'application/x-pdf': PDF,
		'application/msword': DOC,
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DOCX,
		'application/vnd.oasis.opendocument.text': ODT,
		'application/rtf': RTF,
		'application/x-rtf': RTF,
		'text/richtext': RTF,
		'text/rtf': RTF,
		'text/plain': TXT
	}

	extToTypeDict = {
		'pdf': PDF,
		'doc': DOC,
		'dot': DOC,
		'docx': DOCX,
		'docm': DOCX,
		'dotx': DOCX,
		'dotm': DOCX,
		'odt': ODT,
		'fodt': ODT,
		'rtf': RTF,
		'txt': TXT
	}

class File:
	"""Represents a file downloaded from somewhere.
	"""
	success   = False

	def __init__(self,localFile):
			self.localFile = localFile
			self.mimeType  = None

			import urllib2
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
				self._determineMime()
			else:
				logging.warning("Failed to get file")

	def _determineMime(self):
		import magic
		magicMime = magic.Magic(mime=True)
		self.mimeType = magicMime.from_file(self.localFile)

	def exists(self):
		if os.path.isfile(self.localFile):
			return True
		else:
			return False

	def delete(self):
		os.unlink(self.localFile)

	def getFileType(self):
		return FileType.mimeToTypeDict.get(self.mimeType,None)


class FileFromWeb(File):
	"""Represents a file downloaded from the web.
	"""
	def __init__(self,
		url,
		localFile,
		userAgent="ProtoKollen; ProtoCollection (http://protokollen.net)"):
			self.localFile = localFile
			self.success   = False
			self.mimeType  = None

			import urllib2
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
				self._determineMime()
			else:
				logging.warning("Failed to download file from %s" % url)

class FileFromS3(File):
	"""Represents a file downloaded from Amazon S3.
	"""
	def __init__(self,key,localFile):
		self.localFile = localFile
		key.get_contents_to_filename(localFile)

	def getFileType(self):#We know this from the extension, no need to check mime type again
		return FileType.extToTypeDict.get(self.localFile.split(".")[-1],None)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()

