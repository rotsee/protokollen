#coding=utf-8

import os
import shutil
from abc import ABCMeta, abstractmethod

from download import FileFromS3, LocalFile

# FIXME: With the new getNextFile and getFile methods, this should
# probably be named Storage instead of Uploader. But one change at a
# time.
class Uploader:
    """Abstract uploader. Subclasses are used for putting files on remote
    servers, and/or retrieving them from the same place.

    All subclasses are initialized with the same set of parameters,
    but some of the parameters might not be needed with all
    subclasses.

    :param accesskey: Any key that identifies the application requesting 
                      access (not needed for local storage)
    :param secret: A secret key for the application requesting access
                      (not needed for local storage)
    :param token: A token, normally retrieved trough a OAuth authorization, 
                  granting access to a particular user with this app (not 
                  needed for S3 or local storage)
    :param path: The path (or bucket) where files are stored within this backend

    """
    __metaclass__ = ABCMeta

    def __init__(self,
                 app_key = None,
                 app_secret = None,
                 token = None,
                 path = "protokollen"
    ):
        pass

    @abstractmethod
    def putFile(self,localFilename, remoteFilename):
        pass

    @abstractmethod
    def putFileFromString(self, string, remoteFilename):
        pass

    @abstractmethod
    def fileExists(self,fullfilename):
        pass

    @abstractmethod
    def getFileListLength(self,path):
        pass


    @abstractmethod
    def getNextFile(self):
        """Iterates through the file store and returns the next available file, in the form of a Key object that identifies the file and storage-dependent metadata."""
        pass

    @abstractmethod
    def getFile(self, key, localFilename):
        """Retrieves a file identified by key, storing it locally as
localFilename."""
        pass
    
    def buildRemoteName(self,
          name,
          ext="",
          path=""):
        """Concatenate path fragments and filename, for e.g.
           Amazon S3, or some other server.
           `path` can be a string, or a list of strings with path fragments
        """
        fullfilename = ""
        if isinstance(path, list):
            for path_fragment in path:#easier than join, as we want a trailing path_separator
                fullfilename += path_fragment + os.sep
        else:
            fullfilename += path
        fullfilename += name
        if ext != "":
            fullfilename += "." + ext
        return fullfilename

class S3Uploader(Uploader):
    """Handles fileupload to Amazon S3 buckets.

    :param accesskey: The access key id
    :param secret: The secret access key
    :param token: Not used for this storage backend
    :param path: The bucket name
    """

    def __init__(self,
                 accesskey,
                 secret,
                 token = None,
                 path="protokollen"):
        import s3
        self.connection = s3.S3Connection(accesskey, secret,path)

    def getFileListLength(self,pathFragment):
        return self.connection.getBucketListLength(pathFragment)

    # this'll return a Key or Key-like object with .filename, .name
    def getNextFile(self):
        return self.connection.getNextFile()

    # this'll retrieve the file identified by key (returned from
    # getNextFile) and return a download.File object with .localFile
    def getFile(self, key, localFilename):
        return FileFromS3(key, localFilename)
        
    def fileExists(self,fullfilename):
        return self.connection.fileExistsInBucket(fullfilename)

    def putFile(self,localFilename,s3name):
        self.connection.putFile(localFilename,s3name)

    def putFileFromString(self, string, s3name):
        self.connection.putFileFromString(string, s3name)


class LocalUploader(Uploader):
    """Handles file "upload" to a local directory

    :param accesskey: Not used
    :param secret: Not used
    :param token: Not used
    :param path: The local filesystem path
    """
    def __init__(self,
                 accesskey=None,
                 secret=None,
                 token=None,
                 path="protokollen"):
        self.path = path

    def getFileListLength(self, pathFragment):
        raise NotImplementedError

    def fileExists(self, fullfilename):
        return os.path.exists(self.path + os.sep + fullfilename)

    def putFile(self, localFilename, remoteFilename):
        path = self.path + os.sep + remoteFilename
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        shutil.copy2(localFilename, path)

    def getNextFile(self):
        path = self.path

        # mimics the modules.s3.Key interface
        class LocalstorageKey(object):
            def __init__(self, bucket, key):
                assert isinstance(key, basestring) # keys are really filename strings
                # bucket is not used
                self.name = key  # full logical path of the file
                self.path_fragments = key.split("/")
                self.filename = self.path_fragments.pop() # filename w/o path
                self.basename, self.extension = os.path.splitext(self.filename) # filename w/o extension and only extension, respectively

                self.localFilename = path + os.sep + key # full physical path of the file
                
        for root, dirs, files in os.walk(self.path):
            for f in files:
                fullpath = root + os.sep + f
                logicpath = fullpath[len(self.path)+1:]
                yield(LocalstorageKey(None, logicpath))

    def getFile(self, key, localFilename):
        # creating the LocalFile object copies the content to localFilename
        return LocalFile(key, localFilename)

    def putFileFromString(self, string, remoteFilename):
        mode = "wb" if isinstance(string, str) else "w"
        path = self.path + os.sep + remoteFilename
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        with open(path, mode) as fp:
            fp.write(string)
    
        
class DropboxUploader(Uploader):
    """Handles fileupload to Dropbox folders. You need to create a Dropbox
     app and authorize it to access your Dropbox.

    :param accesskey: The app key
    :param secret: The app secret
    :param token: The token from the authorization step. If not provided, 
                  this backend will guide you through this step. 
    :param path: The path in the dropbox where files are stored

    """
    def __init__(self,
                 accesskey,
                 secret,
                 token=None,
                 path="protokollen"):
        import dropbox
        if not token:
            print("Steps to create a token here...")
        raise NotImplementedError

    def getFileListLength(self, pathFragment):
        raise NotImplementedError

    def fileExists(self, fullfilename):
        raise NotImplementedError

    def putFile(self, localFilename, remoteFilename):
        raise NotImplementedError


if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
