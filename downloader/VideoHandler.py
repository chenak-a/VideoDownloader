from __future__ import annotations

import json
import os
import re
import threading
import traceback
import urllib.parse
from abc import ABC, abstractmethod
from asyncio import Lock
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from time import sleep

import js2py
from imageio_ffmpeg import count_frames_and_secs, read_frames, write_frames
from requests import Response, get, head
from tqdm import tqdm

from .FileSystemHandler import FileSystemHandler
from .Utils import Utils
from .VideoErrorHandler import VideoErrorhandler


class Format:

    VIDEO: str = "VIDEO"
    AUDIO: str = "AUDIO"

    def isFormat(cls, type: str):
        if (type is cls.AUDIO) or (type is cls.VIDEO):
            return True
        else:
            return False


class AbsHandler(ABC):

    formatType: Format = Format()
    # HTTP use IP/TCP connection average head size is 8kB we want the head size to be 5% of the package so 152KB of data will do the job
    BUFFERMIN = 152000
    MAXTRY = 20
    # max thread Pool size
    MAXTREADPOOLSIZE = 256
    SLICE = 1024

    def __init__(self, fileSystem: FileSystemHandler, utile: Utils):

        self._body: str = None
        self._payload: dict = None

        self._Title: str = None
        self._fileName: str = None
        self._type: str = self.formatType.VIDEO
        self._try: int = 0
        self._threadPoolSize: int = 60
        self._hiddenDir: dict[str, dict] = {}

        # any video type
        self._qualityVideo: int = 0

        self._fileSystem: FileSystemHandler = fileSystem
        self._utils: Utils = utile

    @abstractmethod
    def _setPayload(self) -> None:
        """body payload"""
        pass

    @abstractmethod
    def _videoTitle(self) -> None:
        pass

    def setVideoQuality(self, quality: int):
        self._qualityVideo = quality

    @abstractmethod
    def download(self, url: str) -> None:
        """download video or audio from url

        Args:
            url (str): url
        """
        pass

    @abstractmethod
    def _searchAudio():
        pass

    @abstractmethod
    def _searchVideo():
        pass

    @abstractmethod
    def _fileType():
        pass

    @abstractmethod
    def _checkServerConnection(self):
        pass

    @abstractmethod
    def _saveFile(self):
        pass

    @abstractmethod
    def _combineVideoAudio(self):
        pass

    @abstractmethod
    def _downloadVideo(self):
        pass

    @abstractmethod
    def _downloadAudio(self):
        pass

    def setFormat(self, format: str):
        """Set the file format

        Args:
            format (str): file format VIDEO or AUDIO
        """
        if self.formatType.isFormat(format):
            self._type = format

    def _threadConfig(self, increment: int):
        if increment > self.BUFFERMIN:
            treadPool = (self._threadPoolSize * increment) // self.BUFFERMIN
            self._threadPoolSize = min(self.MAXTREADPOOLSIZE, treadPool)


class Youtube(AbsHandler):
    AUDIOQUALITY = {
        "AUDIO_QUALITY_LOW": 0,
        "AUDIO_QUALITY_MEDIUM": 1,
        "AUDIO_QUALITY_HIGH": 2,
    }
    
    WEBM = "webm"
    MP4 = "mp4"
    
    VIDEOCODEC = {"video/mp4": {"av01": 0, "avc1": 2}, "video/webm": {"vp9": 1}}

    def __init__(
        self,
        fileSystem: FileSystemHandler,
        utile: Utils,
        videoQuality: int = None,
        typeVideo: int = None,
    ):
        super().__init__(fileSystem, utile)
        if videoQuality:
            self._qualityVideo = videoQuality
        if typeVideo:
            self._type = typeVideo
        self.defaultAudioQuality = self.AUDIOQUALITY["AUDIO_QUALITY_MEDIUM"]

    def __getCipherKey(self, jsBody: str) -> str:
        return re.search(r"[\{\d\w\(\)\\.\=\"]*?;(..\...\(.\,..?\)\;){3,}.*?}", jsBody)[
            0
        ]

    def __getCipherAlgorithm(self, functionName: str, jsBody: str) -> str:
        return re.search(r"var " + functionName + "={.*(.|\s)*?}};", jsBody)[0]

    def __getCipherFunctionName(self, cipherKey: str) -> str:
        functionVariable = re.search(r"\w*\.\w*\(a", cipherKey)[0]
        return re.search(r"(\w*)\B\w", functionVariable)[0]

    def __runJsScript(self, data: str, key: str, value: str) -> str:
        script = value + key
        script = script.replace("\n", "")
        try:
            codeCipher = js2py.eval_js(script)
            return codeCipher(data)
        except:
            VideoErrorhandler("something went wrong")

    def __decription(self, data: str) -> str:
        jsUrl = "https://youtube.com/" + re.findall(r'"jsUrl":"(.*?)"', self._body)[0]
        jsBody = get(jsUrl).text
        cipherKey = self.__getCipherKey(jsBody)
        cipherFunctionName = self.__getCipherFunctionName(cipherKey)
        cipherAlgorithm = self.__getCipherAlgorithm(cipherFunctionName, jsBody)
        return self.__runJsScript(data, cipherKey, cipherAlgorithm)

    def __decipherUrl(self, url: str) -> str:
        urlSlice = re.split(r"&", url)
        key = urlSlice[0].replace("s=", "")
        decipherKey = self.__decription(key)
        queryValue = urlSlice[1].replace("sp=", "")
        url = urlSlice[2].replace("url=", "")
        newURL = urllib.parse.unquote(url)
        return newURL + "&" + queryValue + "=" + decipherKey

    def __checkCrypted(self, data: dict) -> dict:
        if "url" not in data:
            data["url"] = self.__decipherUrl(data["signatureCipher"])
        return data

    def __getVideoQuality(self, data: dict) -> int:
        videoQuality = int(re.search(r"\d*", data["qualityLabel"])[0])
        videFileType = re.search(r"\w*\/\w*", data["mimeType"])[0]

        videCompression = re.search(r'codecs="\w*', data["mimeType"])[0].replace(
            'codecs="', ""
        )

        videolevel = self.VIDEOCODEC[videFileType][videCompression]
        return videolevel + int(videoQuality)

    def _searchAudio(self, listData: list, fileType: str) -> dict:
        try:
            audio: tuple[dict, int] = None

            i = len(listData) - 1
            while "audio" in listData[i]["mimeType"]:
                audioQuality = self.AUDIOQUALITY.get(listData[i]["audioQuality"])
                if (
                    not audio
                    or audioQuality >= audio[1]
                    and fileType in listData[i]["mimeType"]
                ):
                    audio = (
                        listData[i],
                        self.AUDIOQUALITY.get(listData[i]["audioQuality"]),
                        listData[i]["mimeType"],
                    )
                if (
                    audio
                    and audio[1] == self.defaultAudioQuality
                    and fileType in audio[2]
                ):
                    break
                i = i - 1

            return audio[0]
        except:
            print(traceback.print_exc())
            raise

    def __defaultVideo(self, foundVideo: dict, defaultVideo: dict) -> dict:
        if foundVideo:
            return foundVideo
        else:
            return defaultVideo

    def _searchVideo(self, videoList: list, quality: int, reverse: bool) -> dict:

        if (videoList == []) or ("qualityLabel" not in videoList[0]):
            return
        if quality == self.__getVideoQuality(videoList[0]):
            return videoList[0]
        else:
            middle = len(videoList) // 2
            if "video" not in videoList[middle]["mimeType"]:
                return videoList[0]
            videoQuality = self.__getVideoQuality(videoList[middle])
            if quality == videoQuality:
                return videoList[middle]
            elif middle == 0:
                return videoList[middle]
            elif bool(quality > videoQuality) != bool(
                reverse and quality < videoQuality
            ):
                video = self._searchVideo(videoList[1:middle], quality, reverse)
                return self.__defaultVideo(video, videoList[len(videoList) - 1])
            else:
                video = self._searchVideo(videoList[middle + 1 :], quality, reverse)
                return self.__defaultVideo(video, videoList[middle])

    def __getVideo(self, streamingData: dict, decrementalSort: str = False) -> dict:
        video = streamingData[len(streamingData) - 1]
        if self._qualityVideo:
            video = self._searchVideo(
                streamingData, self._qualityVideo, decrementalSort
            )

        return self.__checkCrypted(video)

    def __getAudio(self, streamingData: dict) -> dict:
        typeFile = ""
        if self._type == self.formatType.VIDEO:
            typeFile = self._fileType(
                self._hiddenDir[self.formatType.VIDEO]["metaData"]["mimeType"]
            )
        audio = self._searchAudio(streamingData, typeFile)
        return self.__checkCrypted(audio)

    def _fileType(self, data: str) -> str:
        format = re.search(r"\/\w*", data)[0]
        return format.replace("/", "")

    def __downloadSlices(
        self, data: str, start: int, end: int, bar: tqdm, lock: Lock, file: str
    ) -> list:
        response = get(
            data["url"],
            stream=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                "Connection": "Keep-Alive",
                "Upgrade-Insecure-Requests": "1",
                "sec-ch-ua-platform": "Windows",
                "Cache-Control": "no-store",
                "Range": "bytes={0}-{1}".format(str(start), str(end)),
            },
        )
        if response.ok:
            with open(file, "r+b") as binary_file:
                binary_file.seek(start, 1)
                size = end - start
                for byte in response.iter_content(size):
                    try:
                        value = binary_file.write(byte)

                        bar.update(value)
                        bar.refresh()
                    except:
                        print("Error: Could not write")
                        binary_file.close()
                        raise
                bar.update(size)
                bar.refresh()
                binary_file.close()
        else:
            raise VideoErrorhandler(
                "response code / {0} couldn't access to this video {1} will try {2}/{3} again ...".format(
                    str(response.status_code),
                    self._Title[:15],
                    self._try,
                    str(self.MAXTRY),
                )
            )

    def _checkServerConnection(self, data: str) -> Response:
        try:
            response = head(
                data["url"],
                stream=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                    "Connection": "Keep-Alive",
                    "Upgrade-Insecure-Requests": "1",
                    "sec-ch-ua-platform": "Windows",
                    "DNT": "1",
                    "Range": "bytes=0-",
                },
            )
        except:
            VideoErrorhandler(
                "request err couldn't access to this video {1} will try {2}/{3} again ...\r".format(
                    self._Title[:15],
                    self._try,
                    str(self.MAXTRY),
                )
            )

        if not response.ok or int(response.headers["Content-Length"]) == 0:
            raise VideoErrorhandler(
                "response code / {0} couldn't access to this video {1} will try {2}/{3} again ...\r".format(
                    str(response.status_code),
                    self._Title[:15],
                    self._try,
                    str(self.MAXTRY),
                )
            )

        print(
            "Connected to video server {1} : {0}".format(
                self._Title[:30], "\U0001F680"
            ),
        )
        return response

    def __getContentSize(self, data: str) -> int:
        response = self._checkServerConnection(data)
        return int(response.headers["Content-Length"])

    def __getIncrement(self, size: int, increment: int) -> tuple[int, int]:
        start = 0
        end = 0
        while size > end:
            result = end + increment
            if result > size:
                end = size
            else:
                end = result
            yield start, end
            start = end + 1

    def _saveFile(self, data: str, dir: str = None) -> str:
        directory = self._type.lower()
        if dir != None:
            directory = dir
        fileType = self._fileType(data["mimeType"])
        fileName = self._Title + "." + fileType
        size = self.__getContentSize(data)
        self._fileSystem.createDirectory(directory)
        file = self._fileSystem.createFile(size, directory, fileName)
        initialIncrement = ceil(size / self.SLICE)
        increment = max(self.BUFFERMIN, initialIncrement)
        self._threadConfig(increment)
        try:
            lock = threading.Lock()
            with ThreadPoolExecutor(max_workers=self._threadPoolSize) as executor:
                with tqdm(
                    total=size,
                    desc=self._Title[:25],
                    unit="iB",
                    unit_scale=True,
                ) as bar:
                    result = None
                    for start, end in self.__getIncrement(size, increment):
                        result = executor.submit(
                            self.__downloadSlices, data, start, end, bar, lock, file
                        )
                    result.result()
                bar.close()
        except:
            self._fileSystem.cleanPath(file)
            raise VideoErrorhandler("server err")
        return file

    def __getTypeFile(self, data: str) -> str:
        return re.search(r"^\w*", data)[0]

    def __saveInHiddenDir(self, data: dict) -> str:
        directory = "." + self.__getTypeFile(data["mimeType"])
        return self._saveFile(data, directory)

    def _combineVideoAudio(self) -> None:
        self._fileSystem.createDirectory(self._type.lower())
        videoPath = self._hiddenDir[self.formatType.VIDEO]["filePath"]
        audioPath = self._hiddenDir[self.formatType.AUDIO]["filePath"]
        if not os.path.exists(videoPath) or not os.path.exists(audioPath):
            sleep(2)
        gen = read_frames(videoPath)
        metadata = gen.__next__()
        audioBitRate = self._hiddenDir[self.formatType.AUDIO]["metaData"]["bitrate"]
        frameSize = count_frames_and_secs(videoPath)
        write = write_frames(
            videoPath[1:],
            metadata["size"],
            fps=metadata["fps"],
            codec=metadata["codec"],
            audio_path=audioPath,
            audio_codec="libopus",
            input_params=["-vsync", "0", "-thread_queue_size", "1024"],
            output_params=[
                "-cpu-used",
                "8",
                "-rtbufsize",
                "100M",
                "-b:a",
                str(min(audioBitRate, 512000)),
                "-v",
                "quiet",
            ],
        )
        with tqdm(total=frameSize[0]) as bar:
            try:
                write.send(None)
                for frame in gen:
                    write.send(frame)
                    bar.update(1)
            except:
                print(traceback.print_exc())
                print("something went wrong while merging files")
                self._fileSystem.cleanPath(videoPath[1:])
            finally:
                gen.close()
                write.close()
                bar.close()
                for directory, data in self._hiddenDir.items():
                    directoryName = ".{0}".format(directory.lower())
                    removedFile = self._fileSystem.removeFile(data["filePath"])
                    if removedFile:
                        self._fileSystem.removeDirectory(directoryName)

    def __getAudioVideo(self, type: str, streamingData: dict) -> None:
        self._hiddenDir[type] = {}
        result = None
        try:
            if self.formatType.VIDEO == type:
                result = self.__getVideo(streamingData)
            else:
                result = self.__getAudio(streamingData)
            if result != None:
                filetype = self._fileType(result["mimeType"])
                if filetype == self.WEBM:
                    self._hiddenDir[type]["metaData"] = result
                    self._hiddenDir[type]["filePath"] = self.__saveInHiddenDir(result)
                else :
                    print("we could not find the file type we will install available one")
                    self._qualityVideo=0
        except:
            self._hiddenDir.pop(type)
            raise

    def _downloadVideo(self) -> None:
        streamingData = self._payload["streamingData"]
        videoAudio = self.__getVideo(streamingData["formats"], True)
        if str(self._qualityVideo) not in videoAudio["qualityLabel"]:

            # it need to be a webm to be able to combine audio and video
            self._qualityVideo += 1

            for format in [self.formatType.VIDEO, self.formatType.AUDIO]:
                if not self._hiddenDir.__contains__(format):
                    self.__getAudioVideo(format, streamingData["adaptiveFormats"])
                    self._try = 0

            self._combineVideoAudio()

        else:
            self._saveFile(videoAudio)

    def _downloadAudio(self) -> None:
        streamingData = self._payload["streamingData"]
        audio = self.__getAudio(streamingData["adaptiveFormats"])
        self._saveFile(audio)

    def _setPayload(self) -> None:
        try:
            data = re.search(r"var ytInitialPlayerResponse = \{.*\}", self._body)[0]
            payload = data.replace("var ytInitialPlayerResponse = ", "")
            self._payload = json.loads(payload)
        except:
            raise VideoErrorhandler("this url doesn't contain a video")

    def _videoTitle(self) -> None:
        try:
            self._Title = self._payload["videoDetails"]["title"]
            self._Title = re.sub(r"[^\w_. -]|\s", "_", self._Title)
        except:
            raise VideoErrorhandler("we couldn't find video title")

    def fileExists(self) -> bool:
        for fileTypeVideo in self.VIDEOCODEC:
            typeFile = self._fileType(fileTypeVideo)
            if self._fileSystem.checkFileExist(
                self._type.lower(), self._Title + "." + typeFile
            ):
                return True
        return False

    def download(self, url: str) -> None:
        while True:
            try:
                urlResponse = get(url)
                if urlResponse.ok:
                    self._body = urlResponse.text
                    self._setPayload()
                    self._videoTitle()
                    if self.fileExists():
                        print(
                            "this video is already installed 💾 : {0}".format(
                                self._Title[:30]
                            )
                        )
                        break
                    if self._type is self.formatType.VIDEO:
                        self._downloadVideo()
                    else:
                        self._downloadAudio()
                else:
                    raise VideoErrorhandler(
                        "this url {0} is not responding / response code : {1}".format(
                            url, urlResponse.status_code
                        )
                    )
                print(
                    "Downloaded successful enjoy {1} : {0}".format(
                        self._Title[:30], self._utils.getEmoji()
                    )
                )
                break
            except VideoErrorhandler as e:
                if self._try <= self.MAXTRY:
                    self._try += 1
                    print(e.message)
                    if self._try > 10:
                        sleep(5)
                else:
                    print(
                        "we couldn't download {0} try agin later ".format(
                            self._Title[:15]
                        ),
                        end="\r",
                        flush=True,
                    )
                    break
            except Exception:
                print("Youtube made changes to there website")
                print(traceback.format_exc())
                break
