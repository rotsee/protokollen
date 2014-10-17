#coding=utf-8

class Uploader:
    """Abstract uploader. Subclasses are used for putting files on remote servers.
    """

    path_separator = "/"
    """Could be changes to by subclasses for e.g. a Windows server uploader."""

    def __init__(self):
        pass

    def putFile(self,localFilename):
        pass

    def fileExists(self,fullfilename):
        pass

    def getFileListLength(self,path):
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
        if isinstance(path,list):
            for path_fragment in path:#easier than join, as we want a trailing path_separator
                fullfilename += path_fragment + self.path_separator
        else:
            fullfilename += path
        fullfilename += name
        if ext != "":
            fullfilename += "." + ext
        return fullfilename

class S3Uploader(Uploader):
    """Handles fileupload to Amazon S3 buckets.
    """

    def __init__(self,
        aws_access_key_id,
        aws_secret_access_key,
        aws_bucket_name="protokollen"):
        import s3
        self.connection = s3.S3Connection(aws_access_key_id, aws_secret_access_key,aws_bucket_name)

    def getFileListLength(self,pathFragment):
        return self.connection.getBucketListLength(pathFragment)

    def fileExists(self,fullfilename):
        return self.connection.fileExistsInBucket(fullfilename)

    def putFile(self,localFilename,s3name):
        self.connection.putFile(localFilename,s3name)

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()