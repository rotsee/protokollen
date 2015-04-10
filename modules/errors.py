# -*- coding: utf-8 -*-
"""This module contains classes for logging errors. Errors are reported to the
    Error API which is designed as a standalone web app. The Error API notifies
    admins about errors via e-mail when they are reported. The Error API is a
    standalone module because it has to handle errors from both this code base
    and the Maui text analyzer.

    An error report MUST contain a description and an api key. 
    An error report CAN contain:
    - error_type:   a categorization of the error type
    - document:     the document that the error refer to
    - level:        the seriousness. CRITICAL/ERROR/WARNING/INFO/DEBUG
"""

import logging
from settings import error_api_token, error_api_url


class ErrorReport(object):
    """ Represents an error that we want to report to the Error API.
    """

    """ Description is the only mandatory attribute
    """
    def __init__(self, description, error_type=None, document=None, level=None):
        self.description = description
        self.error_type = error_type
        self.document = document
        self.level = level
        

    def post(self):
        """ Submit to the error to the Error API. The request will trigger
            an e-mail notification to admins.
        """
        from urllib2 import Request, urlopen, HTTPError
        import json

        try:
            req = Request(error_api_url)
            req.add_header('Content-Type', 'application/json')

            args = {
                'token': error_api_token,
                'description': self.description,
                'error_type': self.error_type,
                'document': self.document,
                'level': self.level
            }

            urlopen(req, json.dumps(self.args))
            logging.info("Successfully posted an error report")

        except HTTPError, err:
            self.err = err
            logging.error("%s: %s" % (err.code, err.reason))


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
