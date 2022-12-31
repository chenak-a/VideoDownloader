from .VideoHandler import AbsHandler , Youtube
import re
class VideoDownloader:
    
    def __init__(self):
        self.downloader :AbsHandler =None;
        
    def getDomain(self, url :str) -> str:
        domain_com = re.search(r'\w*.com',url)[0]
        return domain_com.replace('.com','')
    
    def downloadVideo(self, url :str,format:str = None) -> None:
        domain = self.getDomain(url)
        if domain == "youtube" :
            self.downloader = Youtube()
        else : return
        if format : self.downloader.setFormat(format)
        self.downloader.download(url)