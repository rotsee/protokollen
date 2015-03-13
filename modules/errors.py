# -*- coding: utf-8 -*-
"""This module contains classes for logging errors. Errors are reported to the
    Error API which is designed as a standalone web app. The Error API notifies
    admins about errors via e-mail when they are reported. The Error API is a
    standalone module because it has to handle errors from both this code base
    and the Maui text analyzer.
"""

import logging
from settings import error_api_token, error_api_url


class ErrorReport(object):
    """ Represents an error that we want to report to the Error API.
    """
    args = {}
    args['error_type'] = None
    args['document'] = None
    args['level'] = None

    """ Description is the only mandatory attribute
    """
    def __init__(self, description):
        self.args['token'] = error_api_token
        self.args['description'] = description

    def post(self):
        """ Submit to the error to the Error API. The request will trigger
            an e-mail notification to admins.
        """
        from urllib2 import Request, urlopen, HTTPError
        import json

        try:
            req = Request(error_api_url)
            req.add_header('Content-Type', 'application/json')

            urlopen(req, json.dumps(self.args))
            logging.info("Successfully posted an error report")

        except HTTPError, err:
            self.err = err
            logging.error("%s: %s" % (err.code, err.reason))


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
