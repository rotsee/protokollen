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

Storage = storage.LocalStorage
"""
 You need to set the credentials below to use an external storage

 To use Dropbox, try
     Storage = storage.DropboxStorage

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

#error_api_token = "your_secret_token"
#error_api_url = "http://your_error_api"
"""
 A token needed to make requests to our own Error API.
"""

document_rules = [
    ("kommunstyrelseprotokoll",
        ("and", [
            ("or", [
                ("header_contains", "protoko"),  # OCR often confuse l with i
                ("header_contains", "sammanträde")
            ]),
            ("or", [
                ("header_contains", "kommunstyrelse"),
                ("header_contains", "regionstyrelse")  # Gotland
            ]),
            ("not",
                ("header_contains", "arbetsutskott")  # Do not include KSAU
             )
        ])
     ),
    ("kallelse",
        ("and", [
            ("header_contains", "kallelse"),
            ("not",
                ("header_contains", "protoko")
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

document_type_settings = {
    'kommunstyrelseprotokoll': {
        'disallow_infixes': True
    }
}

"""
 Various document type specific settings:

 disallow_infixes:
    If set to true, “holes” in a document is not considered separate documents.
    A file where the pages are identified as `ABAAACC` type pages, will be
    stored as [A,C] if disallow_infixes is True for A, otherwise as [A,B,A,C]
    default: False
"""
