from abc import ABC, abstractmethod
import re
import js2py
import json
import urllib.parse
import sys
from requests import get , Response
from .VideoErrorHandler import VideoErrorhandler
class AbsHandler(ABC):
    VIDEO :str = "VIDEO"
    AUDIO :str = "AUDIO"
    def __init__(self):
        self.Title :str = None
        self.urlVideoAudio :map = None
        self.type :str = self.VIDEO
        self.body :str = None
        self.payload :map = None
    
    @abstractmethod
    def getPayload(self)-> None:
        pass
    
    @abstractmethod
    def getSteamedData(self, body :str) -> None:
        pass
    
    def _fetch(self, url :str) -> Response:
        return get(url)    
        
    @abstractmethod
    def download(self,url :str) -> None:
        pass
    
class Youtube(AbsHandler):

    def __getCipherKey(self, jsBody :str) -> str:
        return re.search(r"[\{\d\w\(\)\\.\=\"]*?;(..\...\(.\,..?\)\;){3,}.*?}", jsBody)[0]
    
    def __getCipherAlgorithm(self, functionName :str, body :str) -> str:
        return re.search(r'var '+ functionName +'={.*(.|\s)*?}};',body)[0]
    
    def __getCipherFunctionName(self, cipherKey :str) -> str:
        functionVariable = re.search(r'\w*\.\w*\(a', cipherKey)[0]
        return re.search(r'(\w*)\B\w', functionVariable)[0]
    
    def __runJsScript(self, data :str, key :str, value:str) -> str:
        script = value + key 
        script = script.replace("\n","")
        codeCipher = js2py.eval_js(script)
        return codeCipher(data)
        
    
    def __decription(self,data :str) -> str:
        jsUrl = 'https://youtube.com/'+re.findall(r'"jsUrl":"(.*?)"', self.body)[0]
        jsBody = self._fetch(jsUrl).text
        cipherKey = self.__getCipherKey(jsBody)
        cipherFunctionName = self.__getCipherFunctionName(cipherKey)
        cipherAlgorithm = self.__getCipherAlgorithm(cipherFunctionName,jsBody)
        return self.__runJsScript(data,cipherKey,cipherAlgorithm)
    
    def __searchAudio(self,listAudio :list,format:str = ""):
        audio :tuple[map,int] = None
        audioQuality = {"AUDIO_QUALITY_LOW" : 0,"AUDIO_QUALITY_MEDIUM" : 1,"AUDIO_QUALITY_HIGH":2}
        i = len(listAudio)-1
        while "audio" in listAudio[i]["mimeType"]:
            if (not audio or audioQuality.get(listAudio[i]["audioQuality"]) > audio[1]) and ( (self.type == self.VIDEO and format in listAudio[i]["mimeType"]) or (self.type == self.AUDIO) ) :
                audio = (listAudio[i],audioQuality.get(listAudio[i]["audioQuality"]))    
            if audio[1] == 2 : break
            i = i-1
        
        return audio[0]
    
    def __defaultVideo(self,foundVideo:map,defaultVideo:map) -> map:
        if foundVideo : return foundVideo
        else : return defaultVideo
        
    def __searchVideo(self,videoList :list,quality :int) -> map:
        if (videoList == []) or ( "qualityLabel" not in  videoList[0] )  :return
        videoQualiry = re.search(r'\d*',videoList[0]["qualityLabel"])[0]
        if quality == int(videoQualiry) : return videoList[0]
        else :
            midel = len(videoList)//2
            videoQualiry = re.search(r'\d*',videoList[midel]["qualityLabel"])[0]
            if "qualityLabel" not in  videoList[midel] :return videoList[0]
            if quality == int(videoQualiry) : return videoList[midel]
            elif midel == 0 : return videoList[midel]
            elif quality > int(videoQualiry) :
                video = self.__searchVideo(videoList[1: midel-1],quality) 
                return self.__defaultVideo(video,videoList[0])
            else :
                video = self.__searchVideo(videoList[midel+1:],quality)
                return self.__defaultVideo(video,videoList[midel])
            
            
           
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

    def __getVideoAudio(self,videoQuality :int = 720) -> map:
        streamingData = self.payload['streamingData']
        videoAudio = self.__getVideo(videoQuality,streamingData['formats'])
        if  str(videoQuality) not in videoAudio["quality"]:
            video = self.__getVideo(videoQuality,streamingData['adaptiveFormats'])
            format = re.search(r'\/\w*',video['mimeType'])[0]
            audio = self.__getAudio(format,streamingData['adaptiveFormats'])
            print(video)
            print(audio)
        print(videoAudio)
    
    def getPayload(self) -> None:
        try :
            data = re.search(r'var ytInitialPlayerResponse = \{.*\}',self.body)[0]
            payloead = data.replace("var ytInitialPlayerResponse = ","")
            self.payload = json.loads(payloead)
        except:
            raise VideoErrorhandler("this url doesn't contain a video")
            
    
    def getSteamedData(self) -> None:
        self.getPayload()
        if self.type is self.VIDEO :
            self.__getVideoAudio()
        
    
        
    def download(self, url :str) -> None:
        try :
            urlRespose = self._fetch(url)
            if urlRespose.status_code == 200:
                self.body = urlRespose.text
                self.getSteamedData()     
            else : raise VideoErrorhandler("this url {0} is not responding response code : {1}".format(url,urlRespose.status_code))
        except VideoErrorhandler as e :
            print(e.errors)
        except :
            print("bad url: " + url)
        