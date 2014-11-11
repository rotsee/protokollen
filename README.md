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
 * Firefox (tested with version 32.0 and 33.0) or Chrome (tested with version 38.0)
 * Xvfb (tested with version 1.15.1)
 * [Service-account credentials](https://developers.google.com/console/help/new/#serviceaccounts) from the [Google developers console](https://console.developers.google.com/), if you wish to use Google Spreadsheets as the source for your harvesting. Not needed if you use a local CSV file.
 * python-magic (installed by setup.py) and libmagic (needs to be installed separately)
 * Optionally a database, to keep track of downloaded files. Elastic Search is supported (tested with version 1.0.1)

 The ChromeDriver executable for your OS must be inside the bin directory for Chrome to work.
 Get it from http://chromedriver.storage.googleapis.com/index.html
 Firefox should work out of the box.
 
For extractor.py
----------------
 * wvText and wvSummary from `wv` (tested with version 1.2.1),
   using either `lynx` or `elinks` (but not `links`)
 * AbiWord (tested with version 3.0.0)
 * Tesseract >= version 3.02.02
 * Language data for Tesseract (for Swedish: a file called [`SWE.traineddata`](https://code.google.com/p/tesseract-ocr/downloads/detail?name=swe.traineddata.gz), that must be put in Tesseract's data directory)
 * The Python Imaging Library, PIL (tested with version 2.3)
 * GhostScript (tested with version 9.10)
 * Optionally a database, to store text and metadata. Elastic Search is supported (tested with version 1.0.1)

These scripts have been tested under Ubuntu 14.04 and Debian 7.


Installation
============

 * Clone this repository
 * From the protokollen directory, run `python setup.py develop`
 * Copy `login.template.py` to `login.py`, and all relevant credentials there
 * If using a Google Docs sheet: Copy your Google API p12 file to `google_api.p12` (or specify another path in `login.py`)


Using ProtoCollection
=====================

Harvesting documents
---------------------
The harvesting script `harvest.py` takes a table with URLs and xPath expressions. It will fetch any new, valid files encountered, and put them in a storage, after checking their mime type. uRLs and xPaths can be provided throgh a CSV file, or a Google Spreadsheet document.

Run `python harvest.py --help` for more info on how to feed data into the script, or `pydoc ./harvest.py` (or `pdoc ./harvest.py`) for API help.

[Here is an example csv file](https://github.com/rotsee/protokollen/blob/master/data/xpath_sample_dalarna_and_gavleborg.csv) with xPaths from Dalarna and Gävleborg. The table should contain the following columns:

* `source`: Used to categorize documents. In our case names of municipalities.
* `baseurl`: The starting point for the harvest.
* Zero or more `preclick1`, `preclick2`, ...: xPaths pointing at stuff (e.g. form elements) that need to be clicked in order to access the list of documents. This is only rarely needed, when there is no way to access to real starting point from an URL.
* One or more `dlclick1`, `dlclick2`, ...: xPaths pointing at the links that need too be followed for each download. All paths will be followed recursively:

&nbsp; 

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
The extraction script `extractor.py` will go through files in a storage, and try to extract plain text and metadata from them, page by page. It understands pdf, docx and doc files, and can also do OCR on scanned pdf-files.

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

Many people have contributed to ProtoKollen in various ways. For a list of source code contributions, see [github.com/rotsee/protokollen/graphs/contributors](https://github.com/rotsee/protokollen/graphs/contributors)

Licence
=======
This repository ships with [Tesseract](https://code.google.com/p/tesseract-ocr/) OCR data for Swedish,
released under the [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0),

and an XMP [metadata parser](http://blog.matt-swain.com/post/25650072381/a-lightweight-xmp-parser-for-extracting-pdf-metadata-in) by Matt Swain, released under the MIT license,

and the Chrome [Undisposition plugin](https://chrome.google.com/webstore/detail/undisposition/hjfncfijclafkkfifjelofbeclipplfi), copyright (c) 2012-2013, ciel, released under both the [BSD License](https://code.google.com/p/ctouch/source/browse/COPYING.md), and [Creative Commons CC0](http://creativecommons.org/publicdomain/zero/1.0/),

and the Firefox [InlineDisposition extension](https://addons.mozilla.org/en-US/firefox/addon/inlinedisposition/), copyright [Kai Liu](http://code.kliu.org/), and released under [BSD License](http://opensource.org/licenses/bsd-license.php).

Everything else is copyright © 2014 [Protokollen Contributors](https://github.com/rotsee/protokollen/graphs/contributors), released under the MIT License (MIT).

In short: You can do whatever you want with it,
but we would love to hear from you if you find it useful!


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
