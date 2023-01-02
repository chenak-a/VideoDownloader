from itertools import repeat
import threading
from downloader import VideoDownloader, Format
import concurrent.futures


class Downloader:
    TYPE = Format()

    def __init__(self) -> None:
        self.downloader = VideoDownloader()
        
        self.threadPool = 5

    


def main():
    downloader = VideoDownloader()
    video = [
        "https://www.youtube.com/watch?v=Aqm9kcpBICI",
        "https://www.youtube.com/watch?v=bLhnw4hYZZU",
        "https://www.youtube.com/watch?v=iGLmZvwKudY",
        "https://www.youtube.com/watch?v=5b35haQV7tU",
        "https://www.youtube.com/watch?v=G0x6DJ9eVsM",
        
    ]
    downloader.run(audio=video)


if __name__ == "__main__":
    main()
