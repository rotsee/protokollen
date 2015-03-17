# -*- coding: utf-8 -*-
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
           Keys like `path-file` will be consistent with ElasticSearch's
           `amazon-s3-river` plugin
        """
        try:
            return "-".join(parts)
        except UnicodeDecodeError:
            return u"-".join([unicode(p) for p in parts])

    def delete(self, key):
        """Delete an entry by key, if it exists.
        """
        raise NotImplementedError('must be overridden by child classes')

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

    def exists(self, key):
        """Return a value, or None"""
        raise NotImplementedError('must be overridden by child classes')

    def get(self, key, attr):
        """Return a value, or None"""
        raise NotImplementedError('must be overridden by child classes')

    def get_attribute_with_value(self, attribute, value):
        """Get a list of keys/rows where a attribute/column has
           the specified value.
        """
        raise NotImplementedError('must be overridden by child classes')

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
