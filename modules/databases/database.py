#coding=utf-8
"""This module contains the base class for all document classes.
"""


class Database(object):
    """Base for database classes. Child classes should implement
       a `put` and a `get` method."""

    def __init__(self, table):
        self.table = table
        pass

    def put(self, key, attr, value):
        pass

    def get(self, key, attr):
        pass

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
