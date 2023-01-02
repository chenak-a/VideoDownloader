from abc import ABC, abstractmethod
from asyncio import  Lock
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from math import ceil
import random
import re
import sys
import threading
import traceback
import js2py
import json
import urllib.parse
from requests import get, head, Response
from .VideoErrorHandler import VideoErrorhandler
from time import sleep
import os
from requests.exceptions import RequestException
from tqdm import tqdm
from sys import platform
from imageio_ffmpeg import *
from multiprocessing import cpu_count

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
    MAXTRY = 15
    #max thread Pool size 
    MAXTREADPOOLSIZE = 256
    SLICE = 1024

    def __init__(self):
        self._Title: str = None
        self._fileName :str = None
        self._filetype: str = None
        self._type: str = self.formatType.VIDEO
        self._body: str = None
        self._payload: dict = None
        self._try: int = 0
        self._contentSize :int = None
        self._threadPoolSize :int = 60
        self._hiddenDir :dict = {}
        
        #any video type
        self._qualityVideo :int = 0

    @abstractmethod
    def setPayload(self) -> None:
        """body payload"""
        pass
    def setVideoQuality(self, quality:int):
        self._qualityVideo = quality
         
    def _fetch(self, url: str, **kwargs) -> Response:
        """get request from url

        Args:
            url (str): url

        Returns:
            Response: response object
        """
        return get(url, kwargs)

    @abstractmethod
    def download(self, url: str) -> None:
        """download video or audio from url

        Args:
            url (str): url
        """
        pass

    def setFormat(self, format: str):
        """Set the file format

        Args:
            format (str): file format VIDEO or AUDIO
        """
        if self.formatType.isFormat(format):
            self._type = format


class Youtube(AbsHandler):
    
    
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
        try :
            codeCipher = js2py.eval_js(script)
            return codeCipher(data)
        except:
            VideoErrorhandler("something went wrong")
    def __decription(self, data: str) -> str:
        jsUrl = "https://youtube.com/" + re.findall(r'"jsUrl":"(.*?)"', self._body)[0]
        jsBody = self._fetch(jsUrl).text
        cipherKey = self.__getCipherKey(jsBody)
        cipherFunctionName = self.__getCipherFunctionName(cipherKey)
        cipherAlgorithm = self.__getCipherAlgorithm(cipherFunctionName, jsBody)
        return self.__runJsScript(data, cipherKey, cipherAlgorithm)

    def __searchAudio(self, listData: list):
        audio: tuple[dict, int] = None
        audioQuality = {
            "AUDIO_QUALITY_LOW": 0,
            "AUDIO_QUALITY_MEDIUM": 1,
            "AUDIO_QUALITY_HIGH": 2,
        }
        i = len(listData) - 1
        while "audio" in listData[i]["mimeType"]:
            if (
                not audio or audioQuality.get(listData[i]["audioQuality"]) > audio[1]
            ) and (
                (
                    self._type == self.formatType.VIDEO
                    and self._filetype in listData[i]["mimeType"]
                )
                or (self._type == self.formatType.AUDIO)
            ):
                audio = (listData[i], audioQuality.get(listData[i]["audioQuality"]))
            if audio and audio[1] == 2:
                break
            i = i - 1
        return audio[0]

    def __defaultVideo(self, foundVideo: dict, defaultVideo: dict) -> dict:
        if foundVideo:
            return foundVideo
        else:
            return defaultVideo

    def __searchVideo(self, videoList: list, quality: int) -> dict:
        if (videoList == []) or ("qualityLabel" not in videoList[0]):
            return
        videoQuality = re.search(r"\d*", videoList[0]["qualityLabel"])[0]
        if quality == int(videoQuality):
            return videoList[0]
        else:
            middle = len(videoList) // 2
            videoQuality = re.search(r"\d*", videoList[middle]["qualityLabel"])[0]
            if "video" not in videoList[middle]["mimeType"]:
                return videoList[0]
            if quality == int(videoQuality):
                return videoList[middle]
            elif middle == 0:
                return videoList[middle]
            elif quality > int(videoQuality):
                video = self.__searchVideo(videoList[1 : middle - 1], quality)
                return self.__defaultVideo(video, videoList[0])
            else:
                video = self.__searchVideo(videoList[middle + 1 :], quality)
                return self.__defaultVideo(video, videoList[middle])

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

    def __getVideo(self, streamingData: dict) -> dict:
        video = streamingData[len(streamingData)-1]
        if self._qualityVideo :
            video = self.__searchVideo(streamingData, self._qualityVideo)
        self.__fileType(video)
        self.__setFileName()
        return self.__checkCrypted(video)

    def __getAudio(self, streamingData: dict):
        audio = self.__searchAudio(streamingData)
        return self.__checkCrypted(audio)

    def __createDirectory(self, directory: str) -> None:
        path = os.path.join("", directory)
        if not os.path.exists(path):
            os.mkdir(path)
            if directory[0] == "." and sys.platform.startswith("win"):
                os.system("attrib +H {0}".format(path))

    def __fileType(self, data: str):
        format = re.search(r"\/\w*", data["mimeType"])[0]
        self._filetype = format.replace("/", "")

    def downloadSlices(
        self, data: str, start: int, end: int, bar: tqdm, lock: Lock, directory: str
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
            with open(
                "{0}/".format(directory) + self._fileName, "r+b"
            ) as binary_file:
                binary_file.seek(start, 1)
                size = end - start
                for byte in response.iter_content(size):
                    try:
                        value = binary_file.write(byte)
                        with lock:
                            bar.update(value)
                    except:
                        print("Error: Could not write")
                        raise
                bar.update(size)
        else:
            raise VideoErrorhandler(
                "response code / {0} couldn't access to this video {1} will try {2}/{3} again ...".format(
                    str(response.status_code), self._Title[:15], self._try, str(self.MAXTRY)
                )
            )
    def checkServerConnection(self,data:str):
        
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
        
        if not response.ok or int(response.headers["Content-Length"]) == 0 :
            raise VideoErrorhandler(
                "response code / {0} couldn't access to this video {1} will try {2}/{3} again ...\r".format(
                    str(response.status_code), self._Title[:15], self._try, str(self.MAXTRY)
                )
            )
            
        print("Connected to video server {1} : {0} ".format(self._Title[:30], "\U0001F680"), end='\n')
        return response
    
    def getContentSize(self, data: str) -> int:
        response = self.checkServerConnection(data)
        return int(response.headers["Content-Length"])

    def createFile(self, size: int, dir: str):
        with open("{0}/".format(dir) + self._fileName, "wb") as out:
            out.truncate(size)

    def getIncrement(self, size: int, increment: int):
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

    def getEmoji(self):
        emoji = [
            "\U0001F680",
            "\U0001F311",
            "\U0001F312",
            "\U0001F315",
            "\U0001F31A",
            "\U0001FA90",
            "\U0001F30C",
            "\U0001F32A",
            "\U000026F1",
            "\U000026A1",
            "\U0001F525",
            "\U0001F3AF",
            "\U0001F3AE",
        ]
        return emoji[random.randint(0, len(emoji)-1)]

    def checkFileExist(self):
        path = os.path.join(self._type.lower(), self._fileName)
        return os.path.exists(path)

    def threadConfig(self, increment: int):
        if increment > self.BUFFERMIN:
            treadPool = (self._threadPoolSize * increment) // self.BUFFERMIN
            self._threadPoolSize = min(self.MAXTREADPOOLSIZE, treadPool)
            print(self._threadPoolSize)
    def __setFileName(self):
        self._fileName = self._Title + "." + self._filetype
    def __saveFile(self, data: str, dir: str = None, visible: bool=True):
        
        
        
        if  visible and self.checkFileExist():
            print("this video is already installed 💾 : {0} ".format(self._Title[:30]))
        else:
            size = self.getContentSize(data)
            directory = self._type.lower()
            if dir != None:
                directory = dir
            self.__createDirectory(directory)
            self.createFile(size, directory)
            initialIncrement = ceil(size / self.SLICE)
            increment = max(self.BUFFERMIN, initialIncrement)
            self.threadConfig(increment)
            lock = threading.Lock()
            with ThreadPoolExecutor(max_workers=self._threadPoolSize) as executor:
                with tqdm(
                    total=size,
                    desc=self._Title[:25],
                    unit="iB",
                    unit_scale=True,
                ) as bar:
                    result = None
                    for start, end in self.getIncrement(size, increment):
                        result = executor.submit(
                            self.downloadSlices, data, start, end, bar, lock, directory
                        )
                    result.result()
                bar.close()
            
            print(
                "Downloaded successful enjoy {1} : {0}".format(
                    self._Title[:30], self.getEmoji()
                , end='\n')
            
            )

    def getTypeFile(self, data: str) -> str:
        return re.search(r"^\w*", data["mimeType"])

    
    def saveInHiddenDir(self, data: dict) ->str:
        directory = "." + self.getTypeFile(data)[0]
        self.__saveFile(data, directory,False)
        return directory
        
    def combineVideoAudio(self) -> None:
        self.__createDirectory(self._type.lower())
        videoPath = "{0}/".format(".video") + self._fileName
        audioPath = "{0}/".format(".audio") + self._fileName
        try :

            gen = read_frames(videoPath)
            metadata = gen.__next__()

            frameSize = count_frames_and_secs(videoPath)
            write = write_frames(videoPath[1:]
                                 ,metadata["size"]
                                 ,fps=metadata["fps"]
                                ,input_params=["-thread_queue_size","1024","-cpu-used","3","-strict","-err_detect","ignore_err"]
                                ,codec=metadata["codec"]
                                ,audio_path=audioPath
                                 )
            with tqdm( total=frameSize[0],                  
                        unit="iB",
                        unit_scale=True,) as bar:
                write.send(None) 
                for frame in gen:
                    write.send(frame)
                    bar.update(1)
                write.close() 
                
        except:
            print(traceback.print_exc())
            print("something went wrong while merging files")
        finally:
            gen.close()
            write.close() 
            for dirName in self._hiddenDir.values():
                self.__removeFile(dirName,self._fileName)
        
    def __removeFile(self, directory:str ,filename:str):
        if os.path.exists(directory+"/"+filename):
            os.remove(directory+"/"+filename)
            if not len(os.listdir(directory)):
                os.rmdir(directory)
            
    def __getAudioVideo(self,type:str,streamingData:dict):
        self._hiddenDir[type] = ""
        result = None
        try :
            if self.formatType.VIDEO == type:
                result = self.__getVideo(streamingData)
            else :
                result = self.__getAudio(streamingData)
            if result != None:
                self._hiddenDir[type] = self.saveInHiddenDir(result)
        except :
            self._hiddenDir.pop(type)
            raise
        

        
    def __downloadVideo(self) -> None:
        streamingData = self._payload["streamingData"]
        videoAudio = self.__getVideo( streamingData["formats"])
        if str(self._qualityVideo) not in videoAudio["qualityLabel"]:
            
            for format in [self.formatType.VIDEO,self.formatType.AUDIO]:
                if not self._hiddenDir.__contains__(format) :  
                    self.__getAudioVideo(format,streamingData["adaptiveFormats"])
                    self._try=0
            
            self.combineVideoAudio()
            
        else:
            self.__saveFile(videoAudio)

    def __downloadAudio(self) -> None:
        streamingData = self._payload["streamingData"]
        audio = self.__getAudio(streamingData["adaptiveFormats"])
        self.__fileType(audio)
        self.__setFileName()
        self.__saveFile(audio)

    def setPayload(self) -> None:
        try:
            data = re.search(r"var ytInitialPlayerResponse = \{.*\}", self._body)[0]
            payload = data.replace("var ytInitialPlayerResponse = ", "")
            self._payload = json.loads(payload)
        except:
            raise VideoErrorhandler("this url doesn't contain a video")

    def videoTitle(self) -> None:
        try:
            self._Title = self._payload["videoDetails"]["title"]
            self._Title = re.sub(r"[^\w_. -]|\s", "_", self._Title)
        except:
            raise VideoErrorhandler("we couldn't find video title")

    def download(self, url: str) -> None:
        while True:
            try:
                urlResponse = self._fetch(url)
                if urlResponse.ok:
                    self._body = urlResponse.text
                    self.setPayload()
                    self.videoTitle()
                    if self._type is self.formatType.VIDEO:
                        self.__downloadVideo()
                    else:
                        self.__downloadAudio()
                else:
                    raise VideoErrorhandler(
                        "this url {0} is not responding / response code : {1}".format(
                            url, urlResponse.status_code
                        )
                    )
                break
            except VideoErrorhandler as e:
                if self._try <= self.MAXTRY:
                    self._try += 1
                    print(e.message,end="\r\n")
                    if self._try > 10:
                        sleep(5)
                else:
                    print("we couldn't download {0} try agin later ".format(self._Title[:15]), end='\r', flush=True)
                    break
            except Exception:
                print(traceback.print_exc())
                break