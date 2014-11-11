#coding=utf-8
"""This file contains a fake DB class, for debugging purposes
"""

from modules.databases.database import Database


class DebuggerDB(Database):
    """This class acts like a Database object,
       but dumps stuff to the screen, rather than storing them.
    """

    def __init__(self, server, table):
        self.table = table
        pass

    def put(self, key, attr, value):
        """Will return True if a value was written, or False
        """
        print "Storing %s in %s.%s.%s" % (value, self.table, key, attr)
        return True

    def put_dict(self, key, attr, dict_):
        """Will return True if a value was written, or False
        """
        print "Storing %s in %s.%s.%s" % (dict_, self.table, key, attr)
        return True

    def get(self, key, attr):
        return None

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
