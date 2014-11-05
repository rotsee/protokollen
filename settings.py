#coding=utf-8
"""This file contains some commons settings for all scripts
"""
from modules import storage
from modules.download import FileType

allowedFiletypes = [FileType.PDF, FileType.DOC, FileType.DOCX, FileType.RTF]
"""What filetypes should we download and store?"""

user_agent = "Protokollen (http://protokollen.net)"
"""How do we identify ourselves?"""

Storage = storage.S3Storage
"""
 You need to set the storage parameters in login.py to use an external storage

 To use local storage, try
     Storage = storage.LocalUploader

 To use Dropbox, try
     Storage = storage.DropboxUploader
 (and set the parameters in login.py accordingly)

 To use Amazon S3, try
     Storage = storage.S3Storage
 (and set the parameters in login.py accordingly)
"""

from modules.databases.elasticsearchdb import ElasticSearch
Database = ElasticSearch
"""
 You need to set the database parameters in login.py to use a database.

 Remove or set to None to disable database indexing

 To use ElasticSearch, try
     from modules.databases.elasticsearchdb import ElasticSearch
     Database = ElasticSearch
"""
