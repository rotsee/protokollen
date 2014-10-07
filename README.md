ProtoCollection
===============
ProtoCollection (Swedish: [ProtoKollen](README.sv.md)) is a web service that harvests and analyzes meeting minutes from the 290 Swedish municipal boards (“kommunstyrelse”). The project is funded by Vinnova.

Installation
============

 * Install Firefox (any version should do) and xvfb
 * Clone this repository
 * From the protokollen directory, run `python setup.py develop`
 * Copy `login.template.py` to `login.py`, and add your Amazon S3 credentials there

Using ProtoCollection
=====================

Harvest documents
-----------------
The harvesting script `harvest.py` takes a CSV with URLs and xPath expressions. It will fetch any encountered PDF, MS Word DOC or DOCX file encountered, and store them on Amazon S3.

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