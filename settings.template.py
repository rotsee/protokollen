#coding=utf-8
"""This file contains common settings for all scripts
"""
from modules import storage
from modules.download import FileType

allowedFiletypes = [FileType.PDF,
                    FileType.DOC,
                    FileType.DOCX,
                    FileType.RTF,
                    FileType.HTML]
"""What filetypes should we download and store?"""

user_agent = "Protokollen (http://protokollen.net)"
"""How do we identify ourselves?"""

browser = "firefox"
"""
 Selenium browser to surf the web with.

 To use Chrome instead, try:
     browser = "chrome"
 and add the chromedriver executable to the bin directory. Get if from
 http://chromedriver.storage.googleapis.com/index.html

"""

Storage = storage.LocalUploader
"""
 You need to set the credentials below to use an external storage

 To use Dropbox, try
     Storage = storage.DropboxUploader

 To use Amazon S3, try
     Storage = storage.S3Storage
"""

Database = None
"""
 You need to set the credentials below to use a database.

 Remove or set to None to disable database indexing

 To use ElasticSearch, try
     from modules.databases.elasticsearchdb import ElasticSearch
     Database = ElasticSearch
"""

#access_key_id = None
#secret_access_key = None
#access_token = None
#bucket_name = 'protokollen'
#text_bucket_name = 'protokollen-text'
"""
 Storage settings, for e.g. Amazon S3, Dropbox, etc.

 Use `Storage` above, to choose your preferred method.
"""

#db_server = 'localhost'
#db_port = None
#db_harvest_table = 'files'
#db_extactor_table = 'documents'
"""
 Database credentials.

 Use `Database` above, to chose your preferred db.
"""

#google_client_email = None
#google_p12_file = None
#google_spreadsheet_key = None
"""
 Google API credentials, if you want to use Google Docs
 to define harvesting rules.
"""

document_rules = [
    ("kommunstyrelseprotokoll",
        ("and", [
            ("or", [
                ("header_contains", "protokoll"),
                ("header_contains", "sammanträde")
            ]),
            ("or", [
                ("header_contains", "kommunstyrelse"),
                ("header_contains", "regionstyrelse")  # Gotland
            ]),
            ("not",
                ("header_contains", "arbetsutskott")
             )
        ])
     )
]
"""
 What defines a document? Extractor will look for these words in page headers,
 to determine which pages from a file belong to the same document,
 in case one file contains many documents. Strings are case insensitive.

 Set this no None, or remove, if each file should be considered
 one document.

 Syntax
 ------
 A list of tuples (name, rules), where `rules` are nested lists and tuples:
 "and": [], "or": [], "not": (), "header_contains": ""
"""
