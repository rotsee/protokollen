#coding=utf-8
"""This module contains the base class for all document classes.
"""

from modules.databases.database import Database
from elasticsearch import Elasticsearch


class ElasticSearch(Database):
    """Class for interacting with an ElasticSearch database
    """

    def __init__(self, url, index, doctype, port=9200):
        self.index = index
        self.doctype = doctype
        self.es = Elasticsearch([{
                                 "host": url,
                                 "port": port,
                                 }])

    def put(self, key, attr, value):
        pass

    def get(self, key, attr):
        res = self.es.get(index=self.index, doc_type=self.doctype, id=key)
        return res["_source"][attr]

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
