#coding=utf-8

class Uploader:
	"""Abstract Uploader
	"""
	def __init__(self):
		pass

	def putFil(self,localFilename):
		pass

	def fileExists(self,fullfilename):
		pass

	def getFileListLength(self,path):
		pass

class S3Uploader(Uploader):

	def __init__(self,
		aws_access_key_id,
		aws_secret_access_key,
		aws_bucket_name="protokollen"):
		import s3
		self.connection = s3.S3Connection(aws_access_key_id, aws_secret_access_key,aws_bucket_name)

	def getFileListLength(self,pathFragment):
		return self.connection.getBucketListLength(pathFragment)

	def fileExists(self,fullfilename):
		return self.connection.fileExistsInBucket(fullfilename)

	def putFile(self,localFilename,s3name):
		self.connection.putFile(localFilename,s3name)

if __name__ == "__main__":
	print "This module is only intended to be called from other scripts."
	import sys
	sys.exit()