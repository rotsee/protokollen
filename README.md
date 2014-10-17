ProtoCollection
===============

ProtoCollection (Swedish: [ProtoKollen](README.sv.md)) is a web service that harvests and analyzes meeting minutes from the 290 Swedish municipal boards (“kommunstyrelse”). The project is funded by Vinnova.


Prerequisites
=============

 * An Amazon S3 bucket
 * Command line access to your server
 * Internet connection (even for a dry run)
 * Python2 => 2.5

For harvester.py
----------------
 * Firefox (tested with version 32.0)
 * Xvfb (tested with version 1.15.1)
 * Python Imaging Library (tested with version 2.3)
 * [Service-account credentials](https://developers.google.com/console/help/new/#serviceaccounts) from the [Google developers console](https://console.developers.google.com/), if you wish to use Google Spreadsheets as the source for your harvesting. Not needed if you use a local CSV file.
 * Tesseract > 3.02.01
 * Swedish data for Tesseract (a file called `SWE.traineddata` in current versions, that must be put in Tesseract's data directory)
 * GhostScript

For extractor.py
----------------
 * wvText and wvSummary from `wv` (tested with version 1.2.1),
   using either `lynx` or `elinks` (but not `links`)

These scripts have been tested under Ubuntu 14.04 and Debian 7. Making them run under Windows would probably require some extra hacking.
 

Installation
============

 * Clone this repository
 * From the protokollen directory, run `python setup.py develop`
 * Copy `login.template.py` to `login.py`, and add your Amazon S3 and Google API credentials there,
   as well as the names of the S3 buckets you want to use.
 * Copy your Google API p12 file to `google_api.p12` (or specify another path in `login.py`)


Using ProtoCollection
=====================

Harvesting documents
---------------------
The harvesting script `harvest.py` takes a table with URLs and xPath expressions. It will fetch any valid files encountered, and store them on Amazon S3.

Run `python harvest.py --help` for more info on how to feed data into the script, or `pydoc ./harvest.py` (or `pdoc ./harvest.py`) for API help.

Extracting data from documents
------------------------------
The extraction script `extractor.py` will go through files in an Amazon S3 bucket, and try to extract plain text data from them.

Run `python extractor.py --help` for more info, or `pydoc ./extractor.py` (or `pdoc ./extractor.py`) for API help.

Analyzing data
--------------
TBD


Changelog
=========

 * 0.1: First harvester

Further information might be available in [the Swedish README file](README.sv.md).


Contact
=======
Find us on [www.protokollen.net](http://www.protokollen.net)


Licence
=======
This repository ships with [Tesseract](https://code.google.com/p/tesseract-ocr/) OCR training data for Swedish,
available under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).

Everything else distributed under the MIT License (MIT).
In short: Do whatever you want with it,
but we would love to hear from you if you find it useful!

Copyright © 2014 [Jens Finnäs](https://twitter.com/jensfinnas), [Peter Grensund](https://twitter.com/grensund), [Leo Wallentin](http://leowallentin.se/leo/en)

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