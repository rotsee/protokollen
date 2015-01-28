#coding=utf-8

import os
from io import BytesIO
import shutil
from abc import ABCMeta, abstractmethod

from download import FileFromS3, LocalFile, File


class Storage:
    """Abstract class for file storage.
    Subclasses are used for putting files on remote
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

    sep = "/"
    """Path separator on the storage file system.
       Can be overriden by child classes, e.g. in LocalUploader.
    """

    def __init__(self,
                 app_key=None,
                 app_secret=None,
                 token=None,
                 path="protokollen"
                 ):
        pass

    @abstractmethod
    def put_file(self, localFilename, remoteFilename):
        pass

    @abstractmethod
    def delete_file(self, filename):
        pass

    @abstractmethod
    def put_file_from_string(self, string, remoteFilename):
        pass

    @abstractmethod
    def prefix_exists(self, fullfilename):
        """Prefix is a path and/or part of a filename.
           It is typically used to check for a file, before
           the extension is known.
        """
        pass

    @abstractmethod
    def getFileListLength(self, path):
        pass

    @abstractmethod
    def get_next_file(self):
        """Iterates through the file store and returns the next available file,
           in the form of a Key object that identifies the file and
           storage-dependent metadata.
        """
        pass

    @abstractmethod
    def get_file(self, key, localFilename):
        """Retrieves a file identified by key, storing it locally
           as localFilename, and returning a download.File object
        """
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
            for path_fragment in path:  # easier than join, as we want a trailing path_separator
                fullfilename += path_fragment + self.sep
        else:
            fullfilename += path + self.sep
        fullfilename += name
        if ext != "":
            fullfilename += "." + ext
        return fullfilename


class S3Storage(Storage):
    """Handles file uploads to Amazon S3 buckets. This is the default
    storage backend.

    In order to use this backend, you need to have an Amazon AWS
    account and use the S3 file storage service. You'll need to create two
    different buckets, one for downloaded source documents and one for
    extracted text.

    In login.py, put your AWS Access Key as access_key_id, and your
    AWS Secret Access Key as secret_access_key (you can ignore
    access_token). Finally enter the name of your buckets as
    bucket_name and text_bucket_name, respectively.

    """
    def __init__(self,
                 accesskey,
                 secret,
                 token=None,
                 path="protokollen"):
        import s3
        self.bucket = path
        self.connection = s3.S3Connection(accesskey, secret, path)

    def getFileListLength(self, pathFragment):
        return self.connection.getBucketListLength(pathFragment)

    # this'll return a Key or Key-like object with .filename, .name
    def get_next_file(self):
        for k in self.connection.get_next_file():
            yield k

    # this'll retrieve the file identified by key (returned from
    # get_next_file) and return a download.File object with .localFile
    def get_file(self, key, localFilename):
        return FileFromS3(key, localFilename)

    def delete_file(self, filename):
        return self.connection.delete_key(filename)

    def prefix_exists(self, fullfilename):
        """Check if a file with this prefix exists (path and/or part
           of filename) in our bucket
        """
        return self.connection.fileExistsInBucket(fullfilename)

    def put_file(self, localFilename, s3name):
        self.connection.put_file(localFilename, s3name)

    def put_file_from_string(self, string, s3name):
        self.connection.put_file_from_string(string, s3name)


class FakeKey(object):
    """ Mimics the modules.s3.Key interface
    """
    def __init__(self, bucket, key):
        assert isinstance(key, basestring)  # keys are really filename strings
        # bucket is not used
        self.name = key
        """ /Path/to/file.ext """
        self.path_fragments = key.split("/")
        """ [Path, to] """
        self.filename = self.path_fragments.pop()
        """ file.ext """
        self.basename, self.extension = os.path.splitext(self.filename)
        """ file, ext """


class LocalStorages(Storage):
    """Handles file “uploads” to a local directory.

    In order to use this backend, you first need to uncomment the
    relevant lines in settings.py.

    In login.py, you can ignore  access_key_id,
    secret_access_key and access_token, but the parameters
    bucket_name and text_bucket_name should be set to the path
    where downloaded files and extracted text should be stored (the
    directories will be created if they don't exist).

    """
#    :param accesskey: Not used
#    :param secret: Not used
#    :param token: Not used
#    :param path: The local filesystem path

    sep = os.sep

    def __init__(self,
                 accesskey=None,
                 secret=None,
                 token=None,
                 path="protokollen"):
        self.path = path

    def getFileListLength(self, pathFragment):
        raise NotImplementedError

    def fileExists(self, fullfilename):
        return os.path.exists(self.path + self.sep + fullfilename)

    def prefix_exists(self, prefix):
        raise NotImplementedError

    def put_file(self, localFilename, remoteFilename):
        path = self.path + os.sep + remoteFilename
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        shutil.copy2(localFilename, path)

    def get_next_file(self):
        for root, dirs, files in os.walk(self.path):
            for f in files:
                fullpath = root + os.sep + f
                logicpath = fullpath[len(self.path) + 1:]
                key = FakeKey(None, logicpath)
                key.localFilename = self.path + os.sep + logicpath
                yield(key)

    def get_file(self, key, localFilename):
        # creating the LocalFile object copies the content to localFilename
        return LocalFile(key, localFilename)

    def put_file_from_string(self, string, remoteFilename):
        mode = "wb" if isinstance(string, str) else "w"
        path = self.path + os.sep + remoteFilename
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        with open(path, mode) as fp:
            fp.write(string)


class DropboxStorage(Storage):
    """Handles file uploads to Dropbox folders.

    In order to use this backend, you first need to create a Dropbox
    app at https://www.dropbox.com/developers/apps/. You can use
    permission type App folder so that it only has access to it's own
    files.

    Leave access_token blank at first. The first time you run any
    script which uses this backend, you'll be prompted to authorize
    the app. Follow the instructions, and an access token will be
    printed. Put this as the value of access_token to avoid
    this...

    """
#    :param accesskey: The app key
#    :param secret: The app secret
#    :param token: The token from the authorization step. If not provided,
#                  this backend will guide you through this step.
#    :param path: The path in the dropbox where files are stored
    def __init__(self,
                 accesskey,
                 secret,
                 token=None,
                 path="protokollen"):
        # dropbox api requires "absolute" paths?
        self.path = "/" + path
        import dropbox
        if not token:
            flow = dropbox.client.DropboxOAuth2FlowNoRedirect(accesskey, secret)
            authorize_url = flow.start()
            print '1. Go to: ' + authorize_url
            print '2. Click "Allow" (you might have to log in first)'
            print '3. Copy the authorization code.'
            code = raw_input("Enter the authorization code here: ").strip()
            token, user_id = flow.finish(code)
            print "OK user %s, your token is %s" % (user_id, token)
            print "Paste it into login.py under access_token"
        self.connection = dropbox.client.DropboxClient(token)
        self.connection.account_info()  # test that the OAuth works

    def getFileListLength(self, pathFragment):
        raise NotImplementedError

    def get_next_file(self):
        paths = [self.path]
        while paths:
            path = paths.pop()
            m = self.connection.metadata(path)
            for thing in m['contents']:
                if thing['is_dir']:
                    paths.append(thing['path'])
                else:
                    path = thing['path']
                    yield FakeKey(None, path)

    def get_file(self, key, local_filename):
        out = open(local_filename, "wb")
        print (key.name)
        with self.connection.get_file(key.name) as f:
            out.write(f.read())
            out.close()
        return File(local_filename)

    def prefix_exists(self, prefix):
        raise NotImplementedError

    def fileExists(self, fullfilename):
        try:
            m = self.connection.metadata(self.path + "/" + fullfilename)
            if m['is_dir']:
                return False
            else:
                return True
        except:
            return False

    def put_file(self, local_filename, remote_filename):
        with open(local_filename) as fp:
            self.connection.put_file(self.path + "/" + remote_filename, fp)

    def put_file_from_string(self, string, remote_filename):
        fp = BytesIO(string)
        self.connection.put_file(self.path + "/" + remote_filename, fp)

    def delete_file(self, filename):
        # TODO
        pass

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
