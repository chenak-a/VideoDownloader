from downloader import VideoDownloader , format
def main():
    type = format()
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=7ushg6kQHiQ"]
    for i in video:
        downloader.downloadVideo(i,type.AUDIO)
if __name__ == '__main__':
    main()