
import os
import sys


class FileSystemHandler :
    
    def createFile(self, size: int, dir: str, fileName: str):
        file = "{0}/".format(dir) + fileName
        with open(file, "wb") as out:
            out.truncate(size)
            out.close()
        return file
    
    def checkFileExist(self, directory: str, fileName: str):
        path = os.path.join(directory, fileName)
        return os.path.exists(path)
    
    def createDirectory(self, directory: str) -> None:
        path = os.path.join("", directory)
        if not os.path.exists(path):
            os.mkdir(path)
            if directory[0] == "." and sys.platform.startswith("win"):
                os.system("attrib +H {0}".format(path))
    
    def removeFile(self, filename: str):
        if os.path.exists(filename):
            os.remove(filename)
            return True
        else:
            return False
    
    def removeDirectory(self, directory: str):
        if not len(os.listdir(directory)):
            os.rmdir(directory)