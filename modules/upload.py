#coding=utf-8
from boto.s3.connection import S3Connection as _S3Connection
from boto.s3.key import Key

class S3Connection:
	"""Represents a S3 connection
	"""
	def __init__(self,
		aws_access_key_id,
		aws_secret_access_key,
		aws_bucket_name="protokollen"):
		self._conn = _S3Connection(aws_access_key_id, aws_secret_access_key)
		self._bucket = self._conn.get_bucket(aws_bucket_name)

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

	def putFile(self,localFilename,s3name):
		k = Key(self._bucket)
		k.key = s3name
		k.set_contents_from_filename(localFilename)
