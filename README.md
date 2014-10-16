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


Some of the Python scripts depend on Google Data Python Client, copyright (C) 2006-2010 Google Inc

Google Data Python Client is Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

For more information on the GData Python client library, please see the 
project on code.google.com's hosting service here: 
http://code.google.com/p/gdata-python-client/