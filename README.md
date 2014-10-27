ProtoCollection
===============

ProtoCollection (Swedish: [ProtoKollen](README.sv.md)) is a web service that harvests and analyzes meeting minutes from the 290 Swedish municipal boards (“kommunstyrelse”). The project is funded by Vinnova.


Prerequisites
=============

 * Command line access to your server
 * Internet connection (even for a dry run)
 * Python2 => 2.5

For harvester.py
----------------
 * Firefox (tested with version 32.0 and 33.0)
 * Xvfb (tested with version 1.15.1)
 * [Service-account credentials](https://developers.google.com/console/help/new/#serviceaccounts) from the [Google developers console](https://console.developers.google.com/), if you wish to use Google Spreadsheets as the source for your harvesting. Not needed if you use a local CSV file.
 * python-magic (installed by setup.py) and libmagic (needs to be installed separately)
 
For extractor.py
----------------
 * wvText and wvSummary from `wv` (tested with version 1.2.1),
   using either `lynx` or `elinks` (but not `links`)
 * Tesseract >= version 3.02.02
 * Swedish data for Tesseract (a file called `SWE.traineddata` in current versions, that must be put in Tesseract's data directory)
 * The Python Imaging Library, PIL (tested with version 2.3)
 * GhostScript (tested with version 9.10)

These scripts have been tested under Ubuntu 14.04 and Debian 7. Making them run under Windows would probably require some extra hacking.
 

Installation
============

 * Clone this repository
 * From the protokollen directory, run `python setup.py develop`
 * Copy `login.template.py` to `login.py`, and add your Amazon S3 and Google API credentials there,
   as well as the names of the S3 buckets you want to use to store documents and text files.
 * Copy your Google API p12 file to `google_api.p12` (or specify another path in `login.py`)


Using ProtoCollection
=====================

Harvesting documents
---------------------
The harvesting script `harvest.py` takes a table with URLs and xPath expressions. It will fetch any new, valid files encountered, and put them in a storage. uRLs and xPaths can be provided throgh a CSV file, or a Google Spreadsheet document.

Run `python harvest.py --help` for more info on how to feed data into the script, or `pydoc ./harvest.py` (or `pdoc ./harvest.py`) for API help.

[Here is an example csv file](https://github.com/rotsee/protokollen/blob/master/data/xpath_sample_dalarna_and_gavleborg.csv) with xPaths from Dalarna and Gävleborg. The table should contain the following columns:

 * `source`: Used to categorize documents. In our case names of municipalities.
 * `baseurl`: The starting point for the harvest.
 * Zero or more `preclick1`, `preclick2`, ...: xPaths pointing at stuff (e.g. form elements) that need to be clicked in order to access the list of documents.
 * One or more `dlclick1`, `dlclick2`, ...: xPaths pointing at the links that need too be followed for each download. All paths will be followed recursively:

    url─>preclick1─>preclick2─┬─>dlclick1─┬>dlclick2─>Sålunda kommunstyrelse 2008-01-24.pdf
                              │           ├>dlclick2─>Sålunda kommunstyrelse 2008-03-14.pdf
                              │           ├>dlclick2─>Sålunda kommunstyrelse 2008-05-02.pdf
                              │           ├>dlclick2─>Sålunda kommunstyrelse 2008-06-12.pdf
                              │           └>dlclick2─>Bil. 1: Motion om namnbyte på kommunen.pdf
                              └─>dlclick1─┬>dlclick2─>Ingalunda kommunstyrelse 2008-07-24.pdf
                                          ├>dlclick2─>Ingalunda kommunstyrelse 2008-09-11.pdf
                                          └>dlclick2─>Ingalunda kommunstyrelse 2008-11-26.pdf 

Extracting data from documents
------------------------------
The extraction script `extractor.py` will go through files in an Amazon S3 bucket, and try to extract plain text and metadata from them, page by page. It understands pdf, docx and doc files, and can also do OCR on scanned pdf-files.

Run `python extractor.py --help` for more info, or `pydoc ./extractor.py` (or `pdoc ./extractor.py`) for API help.

TBD:

 * Separate document headers
 * Some very,very basic text analysis, using those headers
 * Store metadata and file pointers in a database
 * Handle each page separately, as files can often contain multiple documents, and documents be spread across multiple files.

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

Many people have contributed to ProtoKollen in various ways. For a list of source code contributions, see [github.com/rotsee/protokollen/graphs/contributors](https://github.com/rotsee/protokollen/graphs/contributors)

Licence
=======
This repository ships with [Tesseract](https://code.google.com/p/tesseract-ocr/) OCR training data for Swedish,
available under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0).

Everything else distributed under the MIT License (MIT).
In short: Do whatever you want with it,
but we would love to hear from you if you find it useful!

Copyright © 2014 [Contributors](https://github.com/rotsee/protokollen/graphs/contributors)

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
