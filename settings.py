#coding=utf-8
"""This file contains some commons settings for all scripts
"""
from modules import storage
from modules.download import FileType

allowedFiletypes = [FileType.PDF, FileType.DOC, FileType.DOCX]
"""What filetypes should we download and store?"""

user_agent = "ProtoKollen; ProtoCollection (http://protokollen.net)"
"""How do we identify ourselves?"""

Storage = storage.S3Storage
"""
 To use local storage, try
 Storage = storage.LocalUploader
 (and set the parameters in login.py accordingly)

 To use Dropbox, try
 Storage = storage.DropboxUploader
 (and set the parameters in login.py accordingly)
"""
