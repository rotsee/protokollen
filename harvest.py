#!/usr/bin/env python2
#coding=utf-8
"""This script will download all files pointed out by a series of URLs
   and xPath expressions, and upload them to an Amazon S3 server.
   Run `./harvest.py --help` for options.
"""

import hashlib
import login
import settings
from os import path
from modules.interface import Interface
from modules.download import FileFromWeb
from modules.surfer import Surfer
from modules.datasheet import CSVFile, GoogleSheet
from modules.utils import is_number

from collections import deque
import copy


def click_through_dlclicks(browser, dlclicks_deque, start_url=None):
    """Move through a deque of xpath expressions (left to right),
       each xpath describing a click necessary to find and download a document.

       `browser` is a surfer.Surfer object.

       Returns all hrefs from the last step (URLs to the actual documents).
       All hrefs are absolute URLs.
    """
    list_of_hrefs = []
    while dlclicks_deque:
        # During the first iteration we should not go to any url,
        # as the current browser view might be the result of a
        # preclick sequence (e.g. posting a form, using a flash
        # control, ajax-load a list on click, interacting with
        # a HTML5 canvas, etc)
        #
        # Just get the list of URLs at the current page
        if start_url is not None:
            browser.surf_to(start_url)
        dlclick = dlclicks_deque.popleft()
        url_list = browser.get_url_list(dlclick)
        """A list of surfer.Url objects"""
        for url in url_list:
            if not url.is_absolute():
                url.make_absolute(browser.selenium_driver.current_url)
            if len(dlclicks_deque) > 0:  # more iterations to do?
                deque_copy = copy.deepcopy(dlclicks_deque)
                list_of_hrefs += click_through_dlclicks(browser,
                                                        deque_copy,
                                                        url.href)
            else:
                list_of_hrefs.append(url.href)
    return list_of_hrefs


def main():
    """Entry point when run from command line.
       Global variables:

       ui: User interface. Has methods to display messages, etc.
       db: A Database object, or None if no database is defined in settings.py
       data_set: A DataSet object with instructions for the harvester
       browser: A Surfer object, e.g. a wrapper for a selenium browser

    """
    command_line_args = [
        {
            "short": "-s", "long": "--super-dry",
            "dest": "superdryrun",
            "action": "store_true",
            "help": "A dry run where we do not even download any files."
        }, {
            "short": "-t", "long": "--tolarated-changes",
            "type": int,
            "default": 1,
            "dest": "tolaratedchanges",
            "metavar": "CHANGES",
            "help": """When should we warn about suspicios changes in the
                       number of protocols?
                       1 means that anything other that zero or one new
                       protocols is considered suspicios."""
        }, {
            "short": "-f", "long": "--file",
            "dest": "filename",
            "help": "Enter a file name, if your data is in a local CSV file."
        }]
    ui = Interface(__file__,
                   """This script will download all files pointed out by
                      a series of URLs and xPath expressions, and upload
                      them to the configured storage service. """,
                   commandLineArgs=command_line_args)

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

    # Setup database for indexing downloaded files,
    # if a database type is defined in settings.py
    try:
        db = settings.Database(login.db_server,
                               login.db_table,
                               "info",
                               port=login.db_port
                               )
    except (TypeError, NameError) as e:
        print e
        db = None
        ui.exit()

#    sudden_change_threshold = ui.args.tolaratedchanges

    Interface.SUPERDRY_MODE = 2  # add an extra level of dryness
    if ui.args.superdryrun:
        ui.info("Running in super dry mode")
        ui.executionMode = Interface.SUPERDRY_MODE

    ui.info("Connecting to storage")
    uploader = settings.Storage(login.access_key_id,
                                login.secret_access_key,
                                login.access_token,
                                login.bucket_name)

    ui.info("Setting up virtual browser")
    try:
        browser = Surfer()
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
        for preclick in preclicks:
            # preclick is often None which is not a valid value
            # for selenium_driver.find_elements_by_xpath
            if preclick is not None:
                ui.debug("Preclicking %s " % preclick)
                try:
                    browser.click_on_stuff(preclick)
                except Exception as e:
                    ui.warning("Could not do preclick in %s (xPath: %s).\
                               Error message was %s" %
                               (municipality, preclick, e))
        ui.debug("Getting URL list from %s" % row["dlclick1"])
        # use filter to make sure our deque doesn't contain any None values
        hrefList = click_through_dlclicks(browser,
                                          deque(filter(None, dlclicks)))
        ui.info("Found %d URLs" % len(hrefList))
        if len(hrefList) == 0:
            ui.warning("No URLs found for %s " % municipality)
        for href in hrefList:
            filename = hashlib.md5(href).hexdigest()
            remote_naked_filename = uploader.buildRemoteName(filename,
                                                             path=municipality)
            """Full path, but without extension.
               We don't know the proper extension until we have checked
               the mime-type ourselves (we don't trust anyone else)
            """
            if uploader.fileExists(remote_naked_filename):
                ui.debug("%s already exists in storage" % href)
                continue  # File already stored

            if ui.executionMode < Interface.SUPERDRY_MODE:
                ui.debug("Downloading file at %s" % href)
                local_naked_filename = path.join("temp", filename)
                download_file = FileFromWeb(href,
                                            local_naked_filename,
                                            settings.user_agent)
                if download_file.success:
                    filetype = download_file.getFileType()
                    if filetype in settings.allowedFiletypes:
                        file_ext = download_file.getFileExt()
                        remote_full_filename = uploader.buildRemoteName(
                            filename,
                            ext=file_ext,
                            path=municipality)
                        if ui.executionMode < Interface.DRY_MODE:
                            uploader.putFile(local_naked_filename,
                                             remote_full_filename)
                            if db is not None:
                                # Use path + filename as db key
                                dbkey = db.create_key([municipality,
                                                      filename + "." + file_ext])
                                db.put(dbkey, "origin", href)
                                db.put(dbkey, "municipality", municipality)
                                if "year" in row and is_number(row["year"]):
                                    db.put(dbkey, "year", row["year"])
                    else:
                        ui.warning("%s is not an allowed mime type"
                                   % download_file.mimeType)
                    download_file.delete()
                else:
                    ui.warning("Download failed for %s" % href)

if __name__ == '__main__':
    main()
