from itertools import repeat
from downloader import VideoDownloader, Format
import concurrent.futures


class Downloader:
    TYPE = Format()

    def __init__(self) -> None:
        self.downloader = VideoDownloader()
        self.threadPool = 5

    def run(self, listVideo: list, type: str):
        self.threadPool = min(self.threadPool, len(listVideo))
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.threadPool
        ) as executor:
            executor.map(self.downloader.downloadVideo, listVideo, repeat(type))


def main():
    downloader = Downloader()
    video = [
    #    "https://www.youtube.com/watch?v=4K4dgno25Ck",
    #    "https://www.youtube.com/watch?v=JFgrckf52Uw",
        "https://www.youtube.com/watch?v=NVH79ehGfY0"
    ]

    downloader.run(video, downloader.TYPE.VIDEO)


if __name__ == "__main__":
    main()
