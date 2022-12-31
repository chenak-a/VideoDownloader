from itertools import repeat
from downloader import VideoDownloader , Format
import concurrent.futures
def main():
    type = Format()
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=WlaGHS_qs58","https://www.youtube.com/watch?v=uN0qoukeZvI&list=PLN68qIdYV64AjOAmJSN3uylEaQzFkq882&index=30","https://www.youtube.com/watch?v=l5zWiMjBQEE&list=PLN68qIdYV64AjOAmJSN3uylEaQzFkq882&index=16"]
    with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
        executor.map(downloader.downloadVideo,video,repeat(type.VIDEO))
    #for i in video:
    #    downloader.downloadVideo(i,type.VIDEO)
if __name__ == '__main__':
    main()