#coding=utf-8
import logging
import os

class File:
	"""A file being downloaded from a server
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
				self.mimeType = magicmime.from_file(self.localFile)
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
		if self.mimeType == 'application/pdf':
			return 'pdf'
		elif self.mimeType == 'application/msword':
			return 'doc'
		elif self.mimeType == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
			return 'docx'
		elif self.mimeType == 'application/vnd.oasis.opendocument.text':
			return 'odt'
		elif self.mimeType == 'text/rtf':
			return 'rtf'
		elif self.mimeType == 'text/plain':
			return 'txt'
		else:
			return None