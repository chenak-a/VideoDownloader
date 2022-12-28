from downloader import VideoDownloader , Format
def main():
    type = Format()
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=7ushg6kQHiQ"]
    for i in video:
        downloader.downloadVideo(i,type.VIDEO)
if __name__ == '__main__':
    main()