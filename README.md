#  VideoDownloader
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

	

<img src = "https://github.githubassets.com/images/mona-loading-dark.gif" height=20/> VideoDownloader is an open source project created to install video or audio from different site 

## :hammer_and_wrench: Installation 

Use python package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
pip install -r requirements.txt
```




## :building_construction: Usage

```python
class Downloader :
    TYPE = Format()
    
    def __init__(self) -> None:
        self.downloader = VideoDownloader()
        self.threadPool = 5
    
    def run(self,listVideo:list,type:str):
        with concurrent.futures.ThreadPoolExecutor(max_workers = self.threadPool) as executor:
            executor.map(self.downloader.downloadVideo,listVideo,repeat(type))
        
def main():
    downloader = Downloader()
    video = ["https://www.youtube.com/watch?v=U0cfJJupyGc&ab_channel=Ar-RahmanTv","https://www.youtube.com/watch?v=nlYCyGaXPW0&ab_channel=UnMusulman"]
    
    downloader.run(video,downloader.TYPE.VIDEO)
    
if __name__ == '__main__':
    main()
```
## :tada: Result

![](http://i.imgur.com/Ssfp7.gif)


