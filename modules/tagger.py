# -*- coding: utf-8 -*-
"""
"""

import logging
from urllib import urlencode
from urllib2 import HTTPError, urlopen, Request
import json

from settings import tagger_api_url, tagger_api_key

class TextTagger(object):
	def _get_topics(self, text, file_name):
		logging.info("Get topics for file %s from TextTagger API" % file_name)
		params = {
			'file_name': file_name,
			'file_content': text,
			'key': tagger_api_key
		}
		data = urlencode(params)
		req = Request(tagger_api_url, data)
		try:
			response = urlopen(req)
			topics = json.load(response)[0]["topics"]

			logging.info("Found %s topics: %s" % (len(topics), ",".join(topics)))

			if len(topics) == 0:
				logging.warning("The TextTagger API did not come up with any tags for %s" % file_name)

		except HTTPError, err:
			logging.error("%s: %s" % (err.code, err.reason))
			topics = []

		return topics

	def __init__(self, text, file_name):
		self.topics = self._get_topics(text, file_name)

