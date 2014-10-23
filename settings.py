#coding=utf-8
"""This file contains some commons settings for all scripts
"""
from modules import upload
from modules.download import FileType
allowedFiletypes = [FileType.PDF, FileType.DOC, FileType.DOCX]

Storage = upload.S3Uploader

# to use local storage, try
# Storage = upload.LocalUploader
# (and set the aws_* parameters in login.py accordingly)

# to use Dropbox, try
# Storage = upload.DropboxUploader
# (and set the aws_* parameters in login.py accordingly)

