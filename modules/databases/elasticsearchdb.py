#coding=utf-8
"""This module contains the base class for all document classes.
"""

from modules.databases.database import Database
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError


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

    def _get_id(self, id):
        try:
            res = self.es.get(index=self.index, doc_type=self.doctype, id=id)
            return res["_source"]
        except NotFoundError:
            return None

    def put(self, key, attr, value):
        body = self._get_id(key) or {}
        body[attr] = value
        self.es.index(index=self.index,
                      doc_type=self.doctype,
                      id=key,
                      body=body)
        pass

    def get(self, key, attr):
        res = self._get_id(key)
        if res is not None and attr in res:
            return res[attr]
        else:
            return None

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
