from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat

from .FileSystemHandler import FileSystemHandler
from .Utils import Utils
from .VideoHandler import AbsHandler, Format, Youtube


class VideoDownloader:
    TYPE = Format()

    def __init__(self):
        self.__downloader: AbsHandler = None
        self.__threadPool: int = 5
        self.__defaultVideoQuality = 0
        self.__file = FileSystemHandler()
        self.__util = Utils()

    def __getDomain(self, url: str) -> str:
        domain_com = re.search(r"\w*.com", url)[0]
        return domain_com.replace(".com", "")

    def setDefaultVideoQuality(self, videoQuality: int) -> None:
        self.__defaultVideoQuality = videoQuality

    def __threadRun(
        self, thread: ThreadPoolExecutor, urlList: list, formatType: str
    ) -> None:
        thread.map(self.downloadVideo, urlList, repeat(formatType))

    def run(self, *, video: list = [], audio: list = []) -> None:
        if len(video) == 0 and len(audio) == 0:
            return
        with ThreadPoolExecutor(max_workers=self.__threadPool) as executor:
            self.__threadRun(executor, video, self.TYPE.VIDEO)
            self.__threadRun(executor, audio, self.TYPE.AUDIO)

    def downloadVideo(self, url: str, typeFormat: str) -> None:
        domain = self.__getDomain(url)
        if domain == "youtube":
            self.downloader = Youtube(
                self.__file, self.__util, self.__defaultVideoQuality, typeFormat
            )
        else:
            return

        self.downloader.download(url)
