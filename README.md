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
def main():
    downloader = VideoDownloader()
    video = [
        "https://www.youtube.com/watch?v=G8h_2bvkHa0",
        "https://www.youtube.com/watch?v=F9Zt4IFOvLI"
    
        
    ]
    audio = [
        "https://www.youtube.com/watch?v=BYRsQvPOv6o"
    ]
    downloader.setDefaultVideoQuality(720)
    downloader.run(video=video,audio=audio)


if __name__ == "__main__":
    main()
```
## :tada: Result

![](http://i.imgur.com/Ssfp7.gif)


