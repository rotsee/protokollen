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
			import urllib2
			self.localFile = localFile
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
			else:
				logging.warning("Failed to download file from %s" % url)
				self.success = False

	def exists(self):
		if os.path.isfile(self.localFile):
			return True
		else:
			return False

	def delete(self):
		os.unlink(self.localFile)
