from itertools import repeat
from downloader import VideoDownloader , Format
import concurrent.futures
def main():
    type = Format()
    downloader = VideoDownloader()
    threadPool = 5
    video = ["https://www.youtube.com/watch?v=U0cfJJupyGc&ab_channel=Ar-RahmanTv","https://www.youtube.com/watch?v=nlYCyGaXPW0&ab_channel=UnMusulman"]
    with concurrent.futures.ThreadPoolExecutor(max_workers = threadPool) as executor:
        executor.map(downloader.downloadVideo,video,repeat(type.VIDEO))

if __name__ == '__main__':
    main()