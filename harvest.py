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

from collections import deque
import copy


def click_through_dlclicks(browser, start_url, dlclicks_deque):
    """Move through a deque of xpath expressions (left to right),
       each xpath describing a click necessary to find and download a document.

       `browser` is a surfer.Surfer object.

       Returns all hrefs from the last step (URLs to the actual documents).
       All hrefs are absolute URLs.
    """
    list_of_hrefs = []
    while dlclicks_deque:
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
                                                        url.href,
                                                        deque_copy)
            else:
                list_of_hrefs.append(url.href)
    return list_of_hrefs


def main():
    """Entry point when run from command line"""
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
            "help": """When should we warn about suspicios changes in the number of protocols?
                       1 means that anything other that zero or one new protocol since
                       last time is considered suspicios."""
        }, {
            "short": "-f", "long": "--file",
            "dest": "filename",
            "help": """Enter a file name, if your data source is a local CSV file.
                       Otherwise, we will look for a Google Spreadsheets ID in login.py."""
        }]
    ui = Interface(__file__,
                   """This script will download all files pointed out by a series of URLs
                      and xPath expressions, and upload them to the configured
                      storage service. """,
                   commandLineArgs=command_line_args)

    if ui.args.filename is not None:
        ui.info("Harvesting from CSV file `%s`" % ui.args.filename)
        data_set = CSVFile(ui.args.filename)
    elif login.google_spreadsheet_key is not None:
        ui.info("Harvesting from Google Spreadsheet`%s`" % login.google_spreadsheet_key)
        data_set = GoogleSheet(
            login.google_spreadsheet_key,
            login.google_client_email,
            login.google_p12_file)
    else:
        ui.error("No local file given, and no Google Spreadsheet key found.  Cannot proceed.")
        ui.exit()

#    sudden_change_threshold = ui.args.tolaratedchanges

    Interface.SUPERDRY_MODE = 2  # add an extra level of dryness
    if ui.args.superdryrun:
        ui.info("Running in super dry mode")
        ui.executionMode = Interface.SUPERDRY_MODE

    ui.info("Connecting to storage")
    uploader = settings.Storage(login.aws_access_key_id,
                                login.aws_secret_access_key,
                                login.aws_access_token,
                                login.aws_bucket_name)

    ui.info("Setting up virtual browser")
    try:
        browser = Surfer()
        run_harvest(data_set, browser, uploader, ui)
    except Exception as e:
        ui.critical("%s: %s" % (type(e), e))
        raise
    finally:
        ui.info("Closing virtual browser")
        browser.kill()


def run_harvest(data_set, browser, uploader, ui):
    data_set.filter(require=["municipality", "url", "dlclick1"])
    data_set.shuffle()  # give targets some rest between requests
    ui.info("Data contains %d rows" % data_set.getLength())
    # ui.debug(data_set.data)
    preclick_headers = data_set.getEnumeratedHeaders("preclick")
    dlclick_headers = data_set.getEnumeratedHeaders("dlclick")
    for row in data_set.getNext():
        municipality = row["municipality"]
        preclicks = row.enumerated_columns(preclick_headers)
        dlclicks = row.enumerated_columns(dlclick_headers)

        ui.info("Processing %s " % municipality)
        browser.surf_to(row["url"])
        for preclick in preclicks:
            # preclick is often None which is not a valid value
            # for selenium_driver.find_elements_by_xpath
            if preclick:
                ui.debug("Preclicking %s " % preclick)
                browser.click_on_stuff(preclick)
        current_url = browser.selenium_driver.current_url
        ui.debug("We are now at the URL %s" % current_url)
        ui.info("Getting URL list")
        # make sure our deque doesn't contain any None values
        hrefList = click_through_dlclicks(browser,
                                          current_url,
                                          deque(filter(None, dlclicks)))
        ui.info("Found %d URLs" % len(hrefList))
        ui.debug(hrefList)
        if len(hrefList) == 0:
            ui.warning("No URLs found for %s " % municipality)
        for href in hrefList:
            filename = hashlib.md5(href).hexdigest()
            remote_naked_filename = uploader.buildRemoteName(filename, path=municipality)
            """Full path, but without extension.
               We don't know the proper extension until we have checked the mime-type ourselves
               (we don't trust anyone else)
            """
            if uploader.fileExists(remote_naked_filename):
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
                        remote_full_filename = uploader.buildRemoteName(
                            filename,
                            ext=download_file.getFileExt(),
                            path=municipality)
                        if ui.executionMode < Interface.DRY_MODE:
                            uploader.putFile(local_naked_filename, remote_full_filename)
                    else:
                        ui.warning("%s is not an allowed mime type" % download_file.mimeType)
                    download_file.delete()
                else:
                    ui.warning("Download failed for %s" % href)

if __name__ == '__main__':
    main()
