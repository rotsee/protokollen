#!/usr/bin/env python2
#coding=utf-8
"""This script will download all files pointed out by a series of URLs
   and xPath expressions, and put them in a storage (e.g. a local folder
   or an Amazon S3 server).

   Run `./harvest.py --help` for options.
"""

import login
import settings

from os import path
from hashlib import md5
from collections import deque
from copy import deepcopy
import json

from modules.interface import Interface
from modules.download import FileFromWeb
from modules.surfer import Surfer
from modules.datasheet import CSVFile, GoogleSheet
from modules.utils import is_number
from modules.databases.debuggerdb import DebuggerDB


def click_through_dlclicks(browser,
                           dlclicks_deque,
                           callback=None):
    """Move through a deque of xpath expressions (left to right),
       each xpath describing a click necessary to find and download a document.

       `browser` is a surfer.Surfer object.

       Executes a callback function on the very last page of each branch
    """
    if len(dlclicks_deque) > 0:
        dlclick = dlclicks_deque.popleft()
        element_list = browser.get_element_list(dlclick)
        for element in element_list:
            new_dlclicks_deque = deepcopy(dlclicks_deque)
            browser.with_open_in_new_window(element,
                                            # Callback function,
                                            # followed by its parameters
                                            # `browser` will be prepended
                                            click_through_dlclicks,
                                            new_dlclicks_deque,
                                            callback=callback
                                            )
    else:
        callback(browser)


def main():
    """Entry point when run from command line.
       Global variables:

       ui: User interface. Has methods to display messages, etc.
       db: A Database object, or None if no database is defined in settings.py
       data_set: A DataSet object with instructions for the harvester
       browser: A Surfer object, e.g. a wrapper for a selenium browser

       Command line options are in harvest_args.py
    """
    ui = Interface(__file__,
                   """This script will download all files pointed out by
                      a series of URLs and xPath expressions, and upload
                      them to the configured storage service. """)

    if ui.args.filename is not None:
        ui.info("Harvesting from CSV file `%s`" % ui.args.filename)
        data_set = CSVFile(ui.args.filename)
    elif login.google_spreadsheet_key is not None:
        ui.info("Harvesting from Google Spreadsheet`%s`" %
                login.google_spreadsheet_key)
        data_set = GoogleSheet(
            login.google_spreadsheet_key,
            login.google_client_email,
            login.google_p12_file)
    else:
        ui.error("No local file given, and no Google Spreadsheet key found.")
        ui.exit()

    ui.info("Setting up db connection for storing data on downloaded files.")
    try:
        db = settings.Database(login.db_server,
                               login.db_harvest_table,
                               "info",
                               port=login.db_port
                               )
    except (TypeError, NameError, AttributeError):
        ui.info("No database setup found, using DebuggerDB")
        db = DebuggerDB(None, login.db_harvest_table or "TABLE")

    Interface.SUPERDRY_MODE = 2  # add an extra level of dryness
    if ui.args.superdryrun:
        ui.info("Running in super dry mode")
        ui.executionMode = Interface.SUPERDRY_MODE

    ui.info("Connecting to file storage")
    uploader = settings.Storage(login.access_key_id, login.secret_access_key,
                                login.access_token, login.bucket_name)

    ui.info("Setting up virtual browser")
    try:
        browser = Surfer()
        ui.debug("Browsing the web with %s" % browser.browser_version)
        run_harvest(data_set, browser, uploader, ui, db)
    except Exception as e:
        ui.critical("%s: %s" % (type(e), e))
        raise
    finally:
        ui.info("Closing virtual browser")
        browser.kill()


def run_harvest(data_set, browser, uploader, ui, db):
    data_set.filter(require=["source", "url", "dlclick1"])
    data_set.shuffle()  # give targets some rest between requests
    ui.info("Data contains %d rows" % data_set.get_length())
    preclick_headers = data_set.get_enumerated_headers("preclick")
    dlclick_headers = data_set.get_enumerated_headers("dlclick")
    for row in data_set.get_next():
        municipality = row["source"]
        preclicks = row.enumerated_columns(preclick_headers)
        dlclicks = row.enumerated_columns(dlclick_headers)

        ui.info("Processing %s at URL %s" % (municipality, row["url"]))
        browser.surf_to(row["url"])
        ui.debug("We are now at %s" % browser.selenium_driver.current_url)

        for preclick in filter(None, preclicks):
            ui.debug("Preclicking %s " % preclick)
            try:
                browser.click_on_stuff(preclick)
            except Exception as e:
                ui.warning("Could not do preclick in %s (xPath: %s).\
                           Error message was %s" %
                           (municipality, preclick, e))

        ui.debug("Getting URL list from %s" % row["dlclick1"])
        url_list = []

        def _append_to_list(browser):
            ui.debug("Adding URL %s" % browser.selenium_driver.current_url)
            url_list.append(browser.selenium_driver.current_url)
        click_through_dlclicks(browser,
                               deque(filter(None, dlclicks)),
                               callback=_append_to_list)
        ui.info("Found %d URLs" % len(url_list))
        if len(url_list) == 0:
            ui.warning("No URLs found for %s " % municipality)

        for url in url_list:
            filename = md5(url).hexdigest()
            remote_naked_filename = uploader.buildRemoteName(filename,
                                                             path=municipality)
            """Full path, but without extension.
               We don't know the proper extension until we have checked
               the mime-type ourselves (we don't trust anyone else)
            """
            if uploader.fileExists(remote_naked_filename):
                ui.debug("%s already exists in storage" % url)
                continue  # File already stored

            if ui.executionMode < Interface.SUPERDRY_MODE:
                ui.debug("Downloading file at %s" % url)
                local_filename = path.join("temp", filename)
                download_file = FileFromWeb(url,
                                            local_filename,
                                            settings.user_agent)
                filetype = download_file.getFileType()
                if filetype in settings.allowedFiletypes and\
                   ui.executionMode < Interface.DRY_MODE:
                    # Upload file
                    file_ext = download_file.getFileExt()
                    uploader.putFile(local_filename,
                                     uploader.buildRemoteName(filename,
                                                              ext=file_ext,
                                                              path=municipality)
                                     )
                    # Store file info in DB
                    # Use path + filename as db key
                    dbkey = db.create_key([municipality,
                                          filename + "." + file_ext])
                    ui.debug("Adding file origin to DB as %s.origin " % dbkey)
                    result = db.put(dbkey, u"origin", url)
                    ui.debug(result)
                    ui.debug("Adding municipality to DB as %s.municipality " % dbkey)
                    result = db.put(dbkey, u"municipality", municipality)
                    ui.debug(result)
                    ui.debug("Adding harvesting data to DB as %s.harvesting_rules " % dbkey)
                    result = db.put(dbkey, u"harvesting_rules", row)
                    ui.debug(result)
                    if "year" in row and is_number(row["year"]):
                        ui.debug("Adding year to DB as %s.year " % dbkey)
                        db.put(dbkey, u"year", row["year"])
                    try:
                        ui.debug("Extracting metadata")
                        extractor = download_file.extractor()
                        # HtmlExtractor will want to know where in the page to
                        # look for content. Send `html` column, if any
                        if "html" in row:
                            extractor.content_xpath = row["html"]
                        meta = extractor.get_metadata()
                        ui.debug("Adding metadata to DB as %s.metadata " % dbkey)
                        result = db.put(dbkey, u"metadata", meta.data, meta.data)
#                        result = db.put(dbkey, u"metadata", meta.data, json.loads(json_obj))
                        ui.debug(result)
                    except Exception as e:
                        ui.error("Could not get metadata from %s. %s" % (dbkey, e))

                else:
                    ui.warning("%s is not an allowed mime type"
                               % download_file.mimeType)
                download_file.delete()

if __name__ == '__main__':
    main()
