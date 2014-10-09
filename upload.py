#coding=utf-8
import logging
from boto.s3.connection import S3Connection
from boto.s3.key import Key

class S3Connection:
	"""Represents a S3 connection
	"""
	def __init__(self,aws_access_key_id,aws_secret_access_key,aws_bucket_name):
	self._conn = S3Connection(aws_access_key_id, aws_secret_access_key)
	self._bucket = self._conn.get_bucket(aws_bucket_name)
