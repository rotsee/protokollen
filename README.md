ProtoCollection
===============
ProtoCollection (Swedish: [ProtoKollen](README.sv.md)) is a web service that harvests and analyzes meeting minutes from the 290 Swedish municipal boards (“kommunstyrelse”). The project is funded by Vinnova.

Prerequisites
=============
 * Firefox (tested with version 32.0)
 * Xvfb (tested with version 1.15.1)
 * An Amazon S3 bucket
 * [Service-account credentials](https://developers.google.com/console/help/new/#serviceaccounts) from the [Google developers console](https://console.developers.google.com/), if you wish to use Google Spreadsheets as the source for your harvesting. Not needed if using a local CSV file.
 * Command line access to your server
 * Internet connection (even for a dry run)
 
Installation
============

 * Clone this repository
 * From the protokollen directory, run `python setup.py develop`
 * Copy `login.template.py` to `login.py`, and add your Amazon S3 and Google API credentials there
 * Copy your Google API p12 file to `google_api.p12` (or specify another path in `login.py`)

Using ProtoCollection
=====================

Harvesting documents
---------------------
The harvesting script `harvest.py` takes a table with URLs and xPath expressions. It will fetch any valid files encountered, and store them on Amazon S3.

For each row in the data table, `harvest.py` will:

1. Open the entry page
2. Do any clicks required to display the list of protocols
3. Scrape the page for paths for the respective protocols
4. For each protocol, if required, click through any intermediate steps to get to the actual download link
5. Check if the file is already at Amazon
6. Otherwise, download the file
7. Check the mime type of the file
8. If it looks like a valid protocol, upload it to Amazon S3

Run `python harvest.py --help` for more info on how to feed data into the script.

Extracting data from documents
------------------------------
TBD

Analyzing data
--------------
TBD

Changelog
=========

 * 0.1: First harvester

Further information might be available in [the Swedish README file](README.sv.md).

Licence
=======
All code is distributed under the MIT License (MIT)

Copyright (c) 2014 [Jens Finnäs](https://twitter.com/jensfinnas), [Peter Grensund](https://twitter.com/grensund), [Leo Wallentin](http://leowallentin.se/leo/en)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.