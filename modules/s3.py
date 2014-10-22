#coding=utf-8
"""This module contains classes for interacting with Amazon S3,
   including an extension for boto.s3.key.Key
"""
from boto.s3.connection import S3Connection as _S3Connection
from boto.s3.key import Key as BotoKey

class Key(BotoKey):
	"""extends the boto.s3.key.Key class with some helpful
	   name splitting features, to get “files” and “folders”.
	   Can take an existing boto Key object, or a key string
	   as it's second argument.
	"""
	def __init__(self,bucket=None, key=None):
		if key is not None:
<<<<<<< HEAD
			if isinstance(key, basestring):#if either string or unicode
=======
                        # key might be a str (ie bytes) or unicode
                        # depending on the exact arguments to
                        # buildRemoteName. 
			if isinstance(key, (str, unicode)):
>>>>>>> ee962b9f5b8934fec6ff1546317f13e3da36c9b5
				super(Key, self).__init__(bucket, key)
				self.name = key
			else:#if initiated with an existing key
				super(Key, self).__init__(bucket, key.name)
				self.name = key.name

			self.path_fragments = self.name.split("/")
			self.filename = self.path_fragments.pop()
			self.extension = self.filename.split(".")[-1]
			self.basename = self.filename.split(".")[0]
		else:
			super(Key, self).__init__(bucket)

class S3Connection(object):
	"""Represents a S3 connection
	"""
	def __init__(self,
		aws_access_key_id,
		aws_secret_access_key,
		aws_bucket_name="protokollen"):
		self._conn = _S3Connection(aws_access_key_id, aws_secret_access_key)
		self._bucket = self._conn.get_bucket(aws_bucket_name)

	def getNextFile(self):
		for key in self._bucket.list():
			yield Key(self._bucket,key)

	def getBucketListLength(self,pathFragment):
		l = self._bucket.list(pathFragment)
		i = 0
		for key in l:
			i += 1
		return i

	def fileExistsInBucket(self,fullfilename):
		if self.getBucketListLength(fullfilename):
			return True
		else:
			return False

	def putFile(self, localFilename, s3name):
		k = Key(self._bucket,s3name)
		k.set_contents_from_filename(localFilename)

	def putFileFromString(self, string, s3name):
		k = Key(self._bucket,s3name)
		k.set_contents_from_string(string)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()
