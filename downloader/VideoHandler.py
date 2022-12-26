from abc import ABC, abstractmethod
import urllib.request
import re
import js2py
import json
import urllib.parse
from requests import get
class AbsHandler(ABC):
    VIDEO :str = "VIDEO"
    AUDIO :str = "AUDIO"
    def __init__(self):
        
        #title
        self.Title :str = None
        
        #url,quality,type,crypted
        self.video :map = None
        self.audio :map = None
        
        #type
        self.type :str = self.VIDEO
        
    @abstractmethod
    def getSteamedData(self, body :str) -> None:
        pass
    
    def _fetch(self, url :str):
        
        req = urllib.request.Request(url)
        req.add_header('Connection', 'keep-alive')
        req.add_header('Accept-Ranges', 'bytes')
        return urllib.request.urlopen(req)
           
                
        
    @abstractmethod
    def download(self,url :str) -> None:
        pass
    
class Youtube(AbsHandler):
    def searchVideo(self,videoList :list,quality :int) -> map:
        
        
        if (videoList == []) or ( "qualityLabel" not in  videoList[0] )  :return
        videoQualiry = re.search(r'\d*',videoList[0]["qualityLabel"])[0]
        if quality >= int(videoQualiry) : return videoList[0]
        else :
            midel = len(videoList)//2
            videoQualiry = re.search(r'\d*',videoList[midel]["qualityLabel"])[0]
            if "qualityLabel" not in  videoList[midel] :return videoList[0]
            if quality == int(videoQualiry) : return videoList[midel]
            elif midel == 0 : return videoList[midel]
            elif quality > int(videoQualiry) :
                return self.searchVideo(videoList[1: midel-1],quality) 
            else :
                value = self.searchVideo(videoList[midel+1:],quality)
                if value : return value
                else : return videoList[midel]
            
            
           
    def decipherUrl(self,url :str,body :str):
        urlSlice = re.split(r'&',url)
        key = urlSlice[0].replace("s=","")
        decipherKey = self.decription(key,body)
        print(key)
        print(decipherKey)
        queryValue = urlSlice[1].replace("sp=","")
        url = urlSlice[2].replace("url=","")
        newURL = urllib.parse.unquote(url)
        return newURL +"&"+ queryValue+ "=" + decipherKey 
        
    def getSteamedData(self,body :str,quality :int = 720) -> None:
        data = re.search(r'var ytInitialPlayerResponse = \{.*\}',body)[0]
        payloead = data.replace("var ytInitialPlayerResponse = ","")
        payloead = json.loads(payloead)
        steamedData = payloead['streamingData']['adaptiveFormats']
        self.video = self.searchVideo(steamedData,quality)
        if "url" not in self.video:
            self.video["url"] = self.decipherUrl(self.video["signatureCipher"],body)
            print(self.video)
            get(self.video["url"]).content        
    
    def getCipherKey(self, body :str) -> str:
        return re.search(r"[\{\d\w\(\)\\.\=\"]*?;(..\...\(.\,..?\)\;){3,}.*?}", body)[0]
    
    def getCipherAlgorithm(self, functionName :str, body :str) -> str:
        return re.search(r'var '+ functionName +'={.*(.|\s)*?}};',body)[0]
    
    def getCipherFunctionName(self, body :str) -> str:
        functionVariable = re.search(r'\w*\.\w*\(a', body)[0]
        return re.search(r'(\w*)\B\w', functionVariable)[0]
    
    def runJsScript(self, data :str, key :str, value:str) -> str:
        script = value + key 
        script = script.replace("\n","")
        codeCipher = js2py.eval_js(script)
        print(script)
        return codeCipher(data)
        
    
    def decription(self,data :str,body :str) -> str:
        jsUrl = 'https://youtube.com/'+re.findall(r'"jsUrl":"(.*?)"', body)[0]
        
        jsBody = self._fetch(jsUrl).read().decode('utf-8')
        
        cipherKey = self.getCipherKey(jsBody)
        
        cipherFunctionName = self.getCipherFunctionName(cipherKey)
        
        cipherAlgorithm = self.getCipherAlgorithm(cipherFunctionName,jsBody)
        return self.runJsScript(data,cipherKey,cipherAlgorithm)

        
        pass
    def download(self, url :str) -> None:
        
        mainBody =self._fetch(url).read().decode('utf-8')
        self.getSteamedData(mainBody)
        
        #site = "https://rr7---sn-cxaaj5o5q5-t0a6.googlevideo.com/videoplayback?expire=1671972630&ei=tvKnY6mBCKWa6QLz_6vQAg&ip=142.119.12.135&id=o-AMiuejfivWbEP4yKAnfdc5Rmaj79FHYYtRKHy5vqoJbC&itag=135&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C278&source=youtube&requiressl=yes&mh=Ru&mm=31%2C26&mn=sn-cxaaj5o5q5-t0a6%2Csn-tt1e7nls&ms=au%2Conr&mv=m&mvi=7&pl=22&initcwndbps=1535000&vprv=1&mime=video%2Fmp4&ns=q02iNeHLENRi18bBJwkV2ywK&gir=yes&clen=6086172&dur=166.366&lmt=1576436449756320&mt=1671950710&fvip=2&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=2311222&n=5GbRlEy0ZAyE-C-sC&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&sig=AOq0QJ8wRgIhAKOwXMVmt7OwnETsx9DFMSfyMtu44l_8yjcyhciIQggtAiEA_EexzBLr3tuUGKwcRBpxHmUVYT-6jO_wVJ8LiTowi5k%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRAIgDZOHGx9vbazxvb6vHABfqHh_TsTs6znjIIFJsRLWT4MCIEqF9GRRwpw4wc442cFjSYoB5ivw7mkCU7-_YlzSmFwB"
        #ra = self._fetch(site)
        #print(site)
        #print(get(site).content)
        #print(ra)
        #self.decription("aasdewqeqwddddddddddd",mainBody)
        pass
        