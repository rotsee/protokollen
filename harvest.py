#!/usr/bin/env python2
#coding=utf-8
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
from modules.download import FileFromWeb, File
from modules.surfer import Surfer
from modules.datasheet import CSVFile, GoogleSheet
from modules.utils import make_unicode
from modules.databases.debuggerdb import DebuggerDB


def click_through_dlclicks(browser,
                           dlclicks_deque,
                           ui=None,
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
                                                ui=ui,
                                                callback=callback,
                                                *args,
                                                **kwargs
                                                )
            except Exception as e:
                if ui is not None:
                    ui.debug("Element not clickable.")
                    print e
                continue

    else:
        callback(browser, **kwargs)


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

    ui.info("Setting up db connection for storing data on downloaded files.")
    try:
        db = settings.Database(settings.db_server,
                               settings.db_harvest_table,
                               "info",
                               port=settings.db_port
                               )
    except (TypeError, NameError, AttributeError):
        ui.info("No database setup found, using DebuggerDB")
        db = DebuggerDB(None, settings.db_harvest_table or "TABLE")

    Interface.SUPERDRY_MODE = 2  # add an extra level of dryness
    if ui.args.superdryrun:
        ui.info("Running in super dry mode")
        ui.executionMode = Interface.SUPERDRY_MODE

    ui.info("Connecting to file storage")
    uploader = settings.Storage(settings.access_key_id,
                                settings.secret_access_key,
                                settings.access_token,
                                settings.bucket_name)

    ui.info("Setting up virtual browser")
    try:
        browser = Surfer(browser=settings.browser, delay=1)
        ui.debug("Browsing the web with %s" % browser.browser_version)
        run_harvest(data_set, browser, uploader, ui, db)
    except Exception as e:
        ui.critical("%s: %s" % (type(e), e))
        raise
    finally:
        ui.info("Closing virtual browser")
        browser.kill()


def do_download(browser, ui, uploader, row, db):
    """Get the file, put it in the storage, and add a db entry for it
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
#        print short_name
#        print make_unicode(short_name)
        try:
            filename = md5(row["source"] + short_name).hexdigest()
        except UnicodeDecodeError:
            filename = md5(row["source"] + make_unicode(short_name)).hexdigest()
        local_filename = url
        download_file = File(url)
        # if we didn't get the file from an URL, we don't know
        # the origin. Use the starting URL
        origin = row["url"]
    else:
        # Did we open the document inline? Get the file from
        # the current URL
        ui.debug("Adding URL %s" % browser.selenium_driver.current_url)
        url = browser.selenium_driver.current_url
        filename = md5(url).hexdigest()
        local_filename = path.join(ui.args.tempdir, filename)
        download_file = FileFromWeb(url, local_filename, settings.user_agent)
        origin = url

    filetype = download_file.get_file_type()
    file_ext = download_file.get_file_extension()
    remote_name = uploader.buildRemoteName(filename,
                                           path=row["source"],
                                           ext=file_ext)
    dbkey = db.create_key([row["source"], filename + "." + file_ext])
    """ Database key is created from municipality and filename"""

    # Return early if a file with this name exists
    # in both storage and DB
    if uploader.prefix_exists(remote_name) and\
       db.get(dbkey) is not None and\
       ui.args.overwrite is not True:
        ui.debug("%s already exists in storage" % url)
        return

    if filetype in settings.allowedFiletypes and\
       ui.executionMode < Interface.DRY_MODE:

        ui.debug("Uploading file to storage")
        uploader.put_file(local_filename, remote_name)

        ui.debug("Storing file data in database")
        db.put(dbkey, u"origin", origin)
        # Should rather be the more generic “source”
        db.put(dbkey, u"municipality", row["source"])
        db.put(dbkey, u"harvesting_rules", row, overwrite=ui.args.overwrite)
        try:
            ui.debug("Extracting metadata")
            extractor = download_file.extractor()
            # HtmlExtractor will want to know where in the page to
            # look for content. Send `html` column, if any
            if "html" in row:
                extractor.content_xpath = row["html"]
            meta = extractor.get_metadata()
            ui.debug(meta.data)
            db.put(dbkey, u"metadata", meta.data, overwrite=ui.args.overwrite)
        except Exception as e:
            ui.error("Could not get metadata from %s. %s" % (dbkey, e))

    else:
        ui.warning("%s is not an allowed mime type or download failed"
                   % download_file.mimeType)

    try:
        download_file.delete()
    except:
        pass


def run_harvest(data_set, browser, uploader, ui, db):
    """ This is a tree step process, for each row in the data set:

        1. Go to a URL
        2. Click zero or more things (typically to post a form),
           needed to arrive at a list of documents, or links to documents
        3. Recursively do a sequence of 1 or more clicks, to reach each
           document. Documents are sometimes spread across multiple files.
    """
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

        for preclick in filter(None, preclicks):
            ui.debug("Preclicking %s " % preclick)
            try:
                browser.click_on_stuff(preclick)
            except Exception as e:
                ui.warning("Could not do preclick in %s (xPath: %s) %s" %
                           (row["source"], preclick, e))

        ui.debug("Getting URL list from %s and on" % row["dlclick1"])
        click_through_dlclicks(browser,
                               deque(filter(None, dlclicks)),
                               callback=do_download,
                               ui=ui,
                               uploader=uploader,
                               row=row,
                               db=db)

if __name__ == '__main__':
    main()
