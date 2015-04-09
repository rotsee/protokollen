#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""This script will download all files pointed out by a series of URLs
   and xPath expressions, and put them in a storage (e.g. a local folder
   or an Amazon S3 server).

   Run `./harvest.py --help` for options.
"""

import settings

from os import path
from hashlib import md5
from collections import deque
from copy import deepcopy

from modules.interface import Interface
from modules.protokollen import Files
from modules.download import FileFromWeb, File
from modules.surfer import Surfer, ConnectionError
from modules.datasheet import CSVFile, GoogleSheet
from modules.utils import make_unicode

ui = Interface(__file__,
               """This script will download all files pointed out by
                  a series of URLs and xPath expressions, and upload
                  them to the configured storage service. """)
"""`ui` is our command line interface."""


def click_through_dlclicks(browser,
                           dlclicks_deque,
                           callback=None,
                           *args,
                           **kwargs):
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
            try:
                browser.with_open_in_new_window(element,
                                                # Callback function,
                                                # followed by its parameters
                                                # `browser` will be prepended
                                                click_through_dlclicks,
                                                new_dlclicks_deque,
                                                callback=callback,
                                                *args,
                                                **kwargs
                                                )
            except Exception as e:
                ui.warning("Element not clickable. %s" % e)
                continue

    else:
        callback(browser, **kwargs)


def main():
    """Entry point when run from command line.
       Variables:

       data_set: A DataSet object with instructions for the harvester
       browser: A Surfer object, e.g. a wrapper for a selenium browser

       Command line options are in harvest_args.py
    """
    if ui.args.filename is not None:
        ui.info("Harvesting from CSV file `%s`" % ui.args.filename)
        try:
            data_set = CSVFile(ui.args.filename)
        except IOError:
            ui.critical("Could not open CSV file %s" % ui.args.filename)
            ui.exit()
    elif settings.google_spreadsheet_key is not None:
        ui.info("Harvesting from Google Spreadsheet`%s`" %
                settings.google_spreadsheet_key)
        data_set = GoogleSheet(
            settings.google_spreadsheet_key,
            settings.google_client_email,
            settings.google_p12_file)
    else:
        ui.error("No local file given, and no Google Spreadsheet key found.")
        ui.exit()

    Interface.SUPERDRY_MODE = 2  # add an extra level of dryness
    if ui.args.superdryrun:
        ui.info("Running in super dry mode")
        ui.executionMode = Interface.SUPERDRY_MODE

    ui.info("Setting up Files connection.")
    files_connection = Files(ui)

    ui.info("Setting up virtual browser")
    browser = Surfer(browser=settings.browser, delay=1)
    try:
        ui.debug("Browsing the web with %s" % browser.browser_version)
        run_harvest(data_set, browser, files_connection)
    except Exception as e:
        ui.error("%s: %s" % (type(e), e))
        raise
    finally:
        ui.info("Closing virtual browser")
        browser.kill()


def do_download(browser, row, files_connection):
    """Get the file, and add it to files_connection
    """
    ui.debug("Starting download at %s" % browser.selenium_driver.current_url)
    if browser.selenium_driver.current_url == "about:blank":
        # No document here? Get it from the downloaded files.
        url = browser.get_last_download()
        if url is None:
            ui.warning("No file open, and nothing downloaded in row %s" % row)
            return None
        else:
            ui.info("The browser downloaded the file %s" % url)
        # Create name from filename *and* municipality,
        # as there is a slight risk of duplicate names.
        # Don't use path, that can be temporary.
        short_name = path.split(url)[-1]
        try:
            old_style_name = md5(row["origin"] +
                                 short_name).hexdigest()
        except UnicodeDecodeError:
            old_style_name = md5(row["origin"] +
                                 make_unicode(short_name)).hexdigest()
        local_filename = url
        download_file = File(url)
        # if we didn't get the file from an URL, we don't know
        # the source. Use the starting URL
        source_url = row["url"]
    else:
        # Did we open the document inline? Get the file from
        # the current URL
        ui.debug("Adding URL %s" % browser.selenium_driver.current_url)
        source_url = browser.selenium_driver.current_url
        old_style_name = md5(source_url).hexdigest()
        local_filename = path.join(ui.args.tempdir, old_style_name)
        download_file = FileFromWeb(source_url, local_filename,
                                    settings.user_agent)

    # Check for old naming convention before storing
    extension = download_file.get_file_extension()
    if not files_connection.exists(row["origin"], old_style_name, extension):
        files_connection.store_file(download_file, row["origin"], source_url)

    try:
        download_file.delete()
    except Exception as e:
        ui.warning("Could not delete temp file %s (%s)" % (local_filename, e))


def run_harvest(data_set, browser, files_connection):
    """ This is a tree step process, for each row in the data set:

        1. Go to a URL
        2. Click zero or more things (typically to post a form),
           needed to arrive at a list of documents, or links to documents
        3. Recursively do a sequence of 1 or more clicks, to reach each
           document. Documents are sometimes spread across multiple files.
    """
    data_set.filter(require=["origin", "url", "dlclick1"])
    data_set.shuffle()  # give targets some rest between requests
    ui.info("Data contains %d rows" % data_set.get_length())
    preclick_headers = data_set.get_enumerated_headers("preclick")
    dlclick_headers = data_set.get_enumerated_headers("dlclick")

    for row in data_set.get_next():
        preclicks = row.enumerated_columns(preclick_headers)
        dlclicks = row.enumerated_columns(dlclick_headers)

        ui.info("Processing %s at URL %s" % (row["origin"], row["url"]))
        try:
            browser.surf_to(row["url"])
        except ConnectionError as e:
            ui.error(e)
            continue

        for preclick in filter(None, preclicks):
            ui.debug("Preclicking %s " % preclick)
            try:
                browser.click_on_stuff(preclick)
            except Exception as e:
                ui.warning("Could not do preclick in %s" % row["url"])

        ui.debug("Getting URL list from %s and on" % row["dlclick1"])
        click_through_dlclicks(browser,
                               deque(filter(None, dlclicks)),
                               callback=do_download,
                               row=row,
                               files_connection=files_connection)

if __name__ == '__main__':
    main()
