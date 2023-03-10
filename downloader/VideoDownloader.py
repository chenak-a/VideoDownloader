from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from itertools import repeat

from .FileSystemHandler import FileSystemHandler
from .Utils import Utils
from .VideoHandler import AbsHandler, Format, Youtube


class VideoQuality(Enum):
    # could be slow, if the video and audio are split into two files it will take time to combine them
    P2160 = 2160
    P1440 = 1440
    P1080 = 1080
    P720 = 720
    P480 = 360
    P240 = 240
    P144 = 144
    #fast mode this take the best video that contain video and audio 
    ANY = 0
    
class VideoDownloader:
    TYPE = Format()
    
    MAX_TREAD_SIZE = 5
    
    def __init__(self):
        self.__downloader: AbsHandler = None
        self.__threadPool: int = self.MAX_TREAD_SIZE
        self.__defaultVideoQuality = VideoQuality.ANY.value
        self.__file = FileSystemHandler()
        self.__util = Utils()

    def __getDomain(self, url: str) -> str:
        domain_com = re.search(r"\w*.com", url)[0]
        return domain_com.replace(".com", "")
    
    def setDefaultVideoQuality(self, Quality: VideoQuality) -> None:
        if Quality.__class__ is VideoQuality :
            self.__defaultVideoQuality = Quality.value
            print(self.__defaultVideoQuality)
        else : 
            print("use VideoQuality enum instead ex : VideoQuality.P720 ")

    def setTreadPoolSize(self,size:int) -> None:
        self.__threadPool = min(self.MAX_TREAD_SIZE,size)
            
    def __threadRun(
        self, thread: ThreadPoolExecutor, urlList: list, formatType: str
    ) -> None:
        thread.map(self.downloadVideo, urlList, repeat(formatType))

    def cleanHiddenDir(self):
        for dir in [self.TYPE.VIDEO,self.TYPE.AUDIO]:
            self.__file.forceDeleteDirectory("."+dir)
    
    def run(self, *, video: list = [], audio: list = []) -> None:
        if len(video) == 0 and len(audio) == 0:
            return
        try :
            with ThreadPoolExecutor(max_workers=self.__threadPool) as executor:
                self.__threadRun(executor, video, self.TYPE.VIDEO)
                self.__threadRun(executor, audio, self.TYPE.AUDIO)
        finally:
            self.cleanHiddenDir()
            
    def downloadVideo(self, url: str, typeFormat: str) -> None:
        domain = self.__getDomain(url)
        if domain == "youtube":
            self.__downloader = Youtube(
                self.__file, self.__util, self.__defaultVideoQuality, typeFormat
            )
        else:
            return

        self.__downloader.download(url)
