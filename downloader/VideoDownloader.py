from itertools import repeat
from .VideoHandler import AbsHandler, Format, Youtube
import re
from concurrent.futures import ThreadPoolExecutor

class VideoDownloader:
    TYPE = Format()
    
    def __init__(self):
        self.__downloader: AbsHandler = None
        self.__threadPool :int = 5
        
    
    def __getDomain(self, url: str) -> str:
        domain_com = re.search(r"\w*.com", url)[0]
        return domain_com.replace(".com", "")
    
    def setVideoQuality(self, quality:int):
        self.__downloader.setVideoQuality(quality)
    
    def __threadRun(self,thread:ThreadPoolExecutor,urlList:list,formatType:str):
            thread.map(self.downloadVideo,urlList,repeat(formatType))
    
    def run(self,*,video:list=[],audio:list=[]):
        if len(video) == 0 and len(audio) == 0 : return
        with ThreadPoolExecutor(max_workers=self.__threadPool) as executor:
            self.__threadRun(executor,video,self.TYPE.VIDEO)
            self.__threadRun(executor,audio,self.TYPE.AUDIO)
        
    def downloadVideo(self, url: str,typeFormat:str) -> None:
        domain = self.__getDomain(url)
        if domain == "youtube":
            self.downloader = Youtube()
        else:
            return
        self.downloader.setFormat(typeFormat)
        self.downloader.download(url)
