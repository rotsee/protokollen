########################################################################
# Storage credentials, if you want to use a remote storage for files   #
# and extracted text chunks                                            #
########################################################################
access_key_id = None
secret_access_key = None
access_token = None
bucket_name = "files"  # For Amazon S3
text_bucket_name = "text"  # For Amazon S3

########################################################################
# Database credentials, if you want to index downloaded files          #
# and extracted texts in a database                                    #
########################################################################
#db_server = 'localhost'
#db_port = 9200
db_harvest_table = 'files'
db_extactor_table = 'text'
#"""Index name (ES), table name (SQL), etc
#   for harvested files and extracted texts, respectively
#"""

########################################################################
# Google API credentials, if you want to fetch your harvesting         #
# instructions from a Google Spreadsheets sheet                        #
########################################################################
#google_client_email = "GOOGLE CLIENT EMAIL"
#google_p12_file = "google_api.p12"
#google_spreadsheet_key = "SPREADSHEETKEY"
