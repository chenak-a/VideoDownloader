from abc import ABC, abstractmethod
from multiprocessing.sharedctypes import synchronized
import re
import js2py
import json
import urllib.parse
from requests import get , Response
from .VideoErrorHandler import VideoErrorhandler
from time import sleep
import os
from tqdm import tqdm

class Format:
    
    VIDEO :str = "VIDEO"
    AUDIO :str = "AUDIO"
    
    def isFormat(cls,type:str):
        if (type is cls.AUDIO) or (type is cls.VIDEO) : return True
        else : return False 

class AbsHandler(ABC):
  
    formatType :Format = Format()
    
    MAXTRY = 15
    
    def __init__(self):
        self._Title :str = None
        self._type :str = self.formatType.VIDEO
        self._body :str = None
        self._payload :map = None
        self._try :int = 0
    
    @abstractmethod
    def setPayload(self)-> None:
        """ body payload
        """
        pass
    
    def _fetch(self, url :str,**kwargs) -> Response:
        """get request from url

        Args:
            url (str): url

        Returns:
            Response: response object
        """
        return get(url,kwargs)    
        
    @abstractmethod
    def download(self,url :str) -> None:
        """ download request from url

        Args:
            url (str): url
        """
        pass
    
    def setFormat(self,format:str):
        """ Set the file format

        Args:
            format (str): file format VIDEO or AUDIO
        """
        if self.formatType.isFormat(format) : 
            self._type = format
            
class Youtube(AbsHandler):
    
    def __getCipherKey(self, jsBody :str) -> str:
        return re.search(r"[\{\d\w\(\)\\.\=\"]*?;(..\...\(.\,..?\)\;){3,}.*?}", jsBody)[0]
    
    def __getCipherAlgorithm(self, functionName :str, jsBody :str) -> str:
        return re.search(r'var '+ functionName +'={.*(.|\s)*?}};',jsBody)[0]
    
    def __getCipherFunctionName(self, cipherKey :str) -> str:
        functionVariable = re.search(r'\w*\.\w*\(a', cipherKey)[0]
        return re.search(r'(\w*)\B\w', functionVariable)[0]
    
    def __runJsScript(self, data :str, key :str, value:str) -> str:
        script = value + key 
        script = script.replace("\n","")
        codeCipher = js2py.eval_js(script)
        return codeCipher(data)
        
    
    def __decription(self,data :str) -> str:
        jsUrl = 'https://youtube.com/'+re.findall(r'"jsUrl":"(.*?)"', self._body)[0]
        jsBody = self._fetch(jsUrl).text
        cipherKey = self.__getCipherKey(jsBody)
        cipherFunctionName = self.__getCipherFunctionName(cipherKey)
        cipherAlgorithm = self.__getCipherAlgorithm(cipherFunctionName,jsBody)
        return self.__runJsScript(data,cipherKey,cipherAlgorithm)
    
    def __searchAudio(self,listData :list,format:str = ""):
        audio :tuple[map,int] = None
        audioQuality = {"AUDIO_QUALITY_LOW" : 0,"AUDIO_QUALITY_MEDIUM" : 1,"AUDIO_QUALITY_HIGH":2}
        i = len(listData)-1
        while "audio" in listData[i]["mimeType"]:
            if (not audio or audioQuality.get(listData[i]["audioQuality"]) > audio[1]) and ( (self._type == self.formatType.VIDEO and format in listData[i]["mimeType"]) or (self._type == self.formatType.AUDIO) ) :
                audio = (listData[i],audioQuality.get(listData[i]["audioQuality"]))    
            if audio and audio[1] == 2 : break
            i = i-1
        
        return audio[0]
    
    def __defaultVideo(self,foundVideo:map,defaultVideo:map) -> map:
        if foundVideo : return foundVideo
        else : return defaultVideo

    def __searchVideo(self,videoList :list,quality :int) -> map:
        if (videoList == []) or ( "qualityLabel" not in  videoList[0] )  :return
        videoQuality = re.search(r'\d*',videoList[0]["qualityLabel"])[0]
        if quality == int(videoQuality) : return videoList[0]
        else :
            middle = len(videoList)//2
            videoQuality = re.search(r'\d*',videoList[middle]["qualityLabel"])[0]
            if "video" not in  videoList[middle]["mimeType"] :return videoList[0]
            if quality == int(videoQuality) : return videoList[middle]
            elif middle == 0 : return videoList[middle]
            elif quality > int(videoQuality) :
                video = self.__searchVideo(videoList[1: middle-1],quality) 
                return self.__defaultVideo(video,videoList[0])
            else :
                video = self.__searchVideo(videoList[middle+1:],quality)
                return self.__defaultVideo(video,videoList[middle])
            
    def __decipherUrl(self,url :str) -> str:
        urlSlice = re.split(r'&',url)
        key = urlSlice[0].replace("s=","")
        decipherKey = self.__decription(key)
        queryValue = urlSlice[1].replace("sp=","")
        url = urlSlice[2].replace("url=","")
        newURL = urllib.parse.unquote(url)
        return newURL +"&"+ queryValue+ "=" + decipherKey 
    
    def __checkCrypted(self,data:map) -> map:
        if "url" not in data : 
            data["url"] = self.__decipherUrl(data["signatureCipher"])
        return data
        
    def __getVideo(self,videoQuality :str,streamingData :map) -> map:
        video = self.__searchVideo(streamingData,videoQuality)
        return  self.__checkCrypted(video)

    def __getAudio(self,format :str,streamingData :map):
        audio = self.__searchAudio(streamingData,format)
        return self.__checkCrypted(audio)
    
    def __checkDirectory(self,directory:str) -> None:
        path = os.path.join("", directory)
        if not os.path.exists(path):
            os.mkdir(path)
    
    def __saveFile(self,data:str):
        format = re.search(r'\/\w*',data['mimeType'])[0]
        fileType = format.replace("/", ".")       
        response = get(data["url"],stream = True,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
                                                       ,"Connection": "Keep-Alive",
                                                       "Upgrade-Insecure-Requests": "1",
                                                       "sec-ch-ua-platform": "Windows",
                                                       "Cache-Control": "no-store"})
        if not response.ok : 
            errMessage = "response code / {0} couldn't access to this video {2} will try {1} again ...".format(str(response.status_code),self._try,self._Title)
            raise VideoErrorhandler(errMessage)
        
        size = int(response.headers["Content-Length"])
        self.__checkDirectory(self._type.lower())
        
        with open("{0}/".format(self._type.lower()) + self._Title + fileType, "wb") as binary_file:
            with tqdm(total=size, desc=self._Title, unit='iB', unit_scale=True) as bar:
                for a in response.iter_content():
                    try :
                        binary_file.write(a)
                        bar.update(len(a))
                    except:
                        pass
            bar.close()
        binary_file.close()
        response.close()
            
    def __downloadVideo(self,videoQuality :int) -> None:
        
        streamingData = self._payload['streamingData']
        videoAudio = self.__getVideo(videoQuality,streamingData['formats'])
        if  str(videoQuality) not in videoAudio["qualityLabel"]:
            video = self.__getVideo(videoQuality,streamingData['adaptiveFormats'])
            format = re.search(r'\/\w*',video['mimeType'])[0]
            audio = self.__getAudio(format,streamingData['adaptiveFormats'])
            #TODO: combine video and audio
            print(video)
            print(audio)
        else: self.__saveFile(videoAudio)
        
    def __downloadAudio(self) -> None:
        streamingData = self._payload['streamingData']
        audio = self.__getAudio(format,streamingData['adaptiveFormats'])
        self.__saveFile(audio)
        
    def setPayload(self) -> None:
        try :
            data = re.search(r'var ytInitialPlayerResponse = \{.*\}',self._body)[0]
            payload = data.replace("var ytInitialPlayerResponse = ","")
            self._payload = json.loads(payload)
        except:
            raise VideoErrorhandler("this url doesn't contain a video")
            
    def videoTitle(self) -> None:
        try:
            self._Title = self._payload["videoDetails"]["title"]
            self._Title = re.sub(r'[^\w_. -]', '_', self._Title)
        except :
            raise VideoErrorhandler("we couldn't find video title")
        
    def download(self, url :str,qualityVideo :int = 360) -> None:
        
        while True:
            try :
                urlResponse = self._fetch(url)
                if urlResponse.ok:
                    self._body = urlResponse.text
                    self.setPayload()
                    self.videoTitle()
                    if self._type is self.formatType.VIDEO : self.__downloadVideo(qualityVideo) 
                    else : self.__downloadAudio()
                else : raise VideoErrorhandler("this url {0} is not responding / response code : {1}".format(url,urlResponse.status_code))
                break
            except  VideoErrorhandler as e  :
                if self._try <= self.MAXTRY : 
                    print(e.message)
                    sleep(5)
                    self._try += 1
                else : 
                    print("we couldn't download {0} try agin later".format(self._Title))
                    break
            except  :
               print("an error occurred")
   
