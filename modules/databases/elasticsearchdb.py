#coding=utf-8
"""This module contains a class for interacting with ElasticSearch
"""

from modules.databases.database import Database
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from datetime import datetime


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

    def put(self, key, attr, value, overwrite=False):
        """Will return True if a value was written, or False
        """
        body = self._get_id(key) or {}
        if overwrite or (attr not in body):
            body[attr] = value
            body["last_updated"] = datetime.now()
            result = self.es.index(index=self.index,
                                   doc_type=self.doctype,
                                   id=key,
                                   body=body)
            return result
        else:
            return False

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
