from abc import ABC, abstractmethod
import urllib.request
import re
import js2py
class AbsHandler(ABC):
    
    def __init__(self):
        self.quality :map = {}
        
    @abstractmethod
    def getQuality(self, body :str) -> None:
        pass
    
    def _fetch(self, url :str) -> str:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as f:
            return f.read().decode('utf-8')
        
    @abstractmethod
    def download(self,url :str) -> None:
        pass
    
class Youtube(AbsHandler):
    
    def getQuality(self,body :str) -> None:
        pass
    
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
        print(codeCipher(data))
        pass
    
    def decription(self,data :str,body :str) -> str:
        jsUrl = 'https://youtube.com/'+re.findall(r'"jsUrl":"(.*?)"', body)[0]
        jsBody = self._fetch(jsUrl)
        
        cipherKey = self.getCipherKey(jsBody)
        cipherFunctionName = self.getCipherFunctionName(cipherKey)
        cipherAlgorithm = self.getCipherAlgorithm(cipherFunctionName,jsBody)
        data = self.runJsScript(data,cipherKey,cipherAlgorithm)
        
        
        pass
    def download(self, url :str) -> None:
        mainBody = self._fetch(url)
        self.decription("aasdewqeqwddddddddddd",mainBody)
        pass
        