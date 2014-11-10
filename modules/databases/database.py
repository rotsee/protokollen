#coding=utf-8
"""This module contains the base class for all database classes.
"""


class Database(object):
    """Base for database classes. Child classes should implement
       a `put` and a `get` method.
    """

    def __init__(self, server, table, category=None, port=None):
        """Table i a SQL table, ES index, etc.
           Category, if used, is a ES document type, or similar.
        """
        self.table = table
        pass

    def create_key(self, parts=None):
        """We might want keys to correspond somehow to filenames and paths.
           For instance, if we create keys like `path-file`, they will be
           consistent with ElasticSearch's `amazon-s3-river` plugin, see
           https://github.com/lbroudoux/es-amazon-s3-river/blob/master/src/main/java/com/github/lbroudoux/elasticsearch/river/s3/river/S3River.java#LC508
        """
        return "-".join(parts)

    def put(self, key, attr, value):
        raise NotImplementedError('must be overridden by child classes')

    def put_dict(self, key, attr, dict_):
        """Should normally be overwritten by child classes, to use a more
           efficient method.
        """
        success = False
        for (k, v) in dict_.iteritems():
            success = success and self.put(key, k, v)
        return success

    def get(self, key, attr):
        raise NotImplementedError('must be overridden by child classes')

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
