from itertools import repeat
from downloader import VideoDownloader , Format
import concurrent.futures
def main():
    type = Format()
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=CJYiI_UdzFU","https://www.youtube.com/watch?v=FRbcxja3DC0"]
    with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
        executor.map(downloader.downloadVideo,video,repeat(type.AUDIO))
if __name__ == '__main__':
    main()