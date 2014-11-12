#coding=utf-8
import logging
import os
import shutil

from modules.extractors.pdf import PdfExtractor
from modules.extractors.ooxml import DocxExtractor
from modules.extractors.doc import DocExtractor
from modules.extractors.rtf import RtfExtractor
from modules.extractors.html import HtmlExtractor


class FileType:
    UNKNOWN = 0
    PDF = 1
    DOC = 2
    DOCX = 3
    ODT = 4
    RTF = 5
    TXT = 6
    HTML = 7

    mime_to_type_dict = {
        'application/pdf': PDF,
        'application/x-pdf': PDF,
        'application/msword': DOC,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DOCX,
        'application/vnd.oasis.opendocument.text': ODT,
        'application/rtf': RTF,
        'application/x-rtf': RTF,
        'text/richtext': RTF,
        'text/rtf': RTF,
        'text/plain': TXT,
        'text/html': HTML,
        'text/x-server-parsed-html': HTML,
        'application/xhtml+xml': HTML
    }

    ext_to_type_dict = {
        'pdf': PDF,
        'doc': DOC,
        'dot': DOC,
        'docx': DOCX,
        'docm': DOCX,
        'dotx': DOCX,
        'dotm': DOCX,
        'odt': ODT,
        'fodt': ODT,
        'rtf': RTF,
        'txt': TXT,
        'htm': HTML,
        'html': HTML,
        'htm': HTML,
        'html': HTML,
        'xhtml': HTML
    }

    type_to_ext_dict = {
        UNKNOWN: None,
        PDF: "pdf",
        DOC: "doc",
        DOCX: "docx",
        ODT: "odt",
        RTF: "rtf",
        TXT: "txt",
        HTML: "html"
    }

    type_to_extractor_dict = {
        PDF: PdfExtractor,
        DOCX: DocxExtractor,
        DOC: DocExtractor,
        RTF: RtfExtractor,
        HTML: HtmlExtractor
    }


class File(object):
    """Represents a file downloaded from somewhere.
    """
    success = False

    def __init__(self, source, localFile):
            self.localFile = localFile
            self.mimeType = None

    def _determineMime(self):
        import magic
        magicMime = magic.Magic(mime=True)
        self.mimeType = magicMime.from_file(self.localFile)

    def exists(self):
        if os.path.isfile(self.localFile):
            return True
        else:
            return False

    def delete(self):
        os.unlink(self.localFile)

    def getFileType(self):
        """ This default method only uses the extension of the file, not
            self.mimeType (which only gets set by the subclass
            FileFromWeb, which uses an alternate implementation of this method)
        """
        return FileType.ext_to_type_dict.get(self.localFile.split(".")[-1],
                                             None)

    def getFileExt(self):
        return FileType.type_to_ext_dict.get(self.getFileType(), None)

    def extractor(self, **kwargs):
        """Returns an extractor object suitable for analyzing this file
        """
        Extractor = FileType.type_to_extractor_dict.get(self.getFileType(),
                                                        None)
        extractor = Extractor(self.localFile, **kwargs)
        return extractor


class LocalFile(File):
    def __init__(self, source, localFile):
                super(LocalFile, self).__init__(source, localFile)
                shutil.copy2(source.localFilename, localFile)


class DropboxFile(File):
        def __init__(self, source, localFile):
                super(DropboxFile, self).__init__(source, localFile)
                out = open(localFile, "wb")
                with source.dbclient.get_file(source.rootpath + "/" + source.name) as f:
                        out.write(f.read())
                out.close()


class FileFromWeb(File):
    """Represents a file downloaded from the web.
    """
    def __init__(self,
                 url,
                 localFile,
                 userAgent='Mozilla/5.0 (compatible)'):
            self.localFile = localFile
            self.success = False
            self.mimeType = None

            import urllib2
            try:
                url = url.encode('utf-8')
                req = urllib2.Request(url)
                req.add_header('User-agent', userAgent)
                f = urllib2.urlopen(req)
                # make sure the directory we're
                # placing the file in actually exists
                d = os.path.dirname(self.localFile)
                if d and not os.path.exists(d):
                        os.makedirs(d)

                with open(self.localFile, "wb") as localFileHandle:
                    localFileHandle.write(f.read())

            except urllib2.HTTPError, e:
                logging.warning("HTTP Error: %s %s" % (e.code, url))
            except urllib2.URLError, e:
                logging.warning("URL Error: %s %s" % (e.reason, url))

            if self.exists():
                self.success = True
                self._determineMime()
            else:
                logging.warning("Failed to download file from %s" % url)

    def getFileType(self):
        """Return filetype based on mimeType
        """
        return FileType.mime_to_type_dict.get(self.mimeType, None)


class FileFromS3(File):
    """Represents a file downloaded from Amazon S3.
    """
    def __init__(self, key, localFile):
        self.localFile = localFile
        key.get_contents_to_filename(localFile)


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
