#coding=utf-8
"""This file contains some commons settings for all scripts
"""
from modules import upload
from modules.download import FileType
allowedFiletypes = [FileType.PDF, FileType.DOC, FileType.DOCX]

# to use local storage, try
# storage = upload.LocalUploader
# (and set the aws_* parameters in login.py accordingly)

# to use Dropbox, try
# storage = upload.DropboxUploader
# (and set the aws_* parameters in login.py accordingly)

Storage = upload.S3Uploader
