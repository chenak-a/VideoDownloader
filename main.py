from downloader.VideoDownloader import  VideoDownloader
def main():
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=7ushg6kQHiQ"]
    for i in video:
        downloader.downloadVideo(i)
if __name__ == '__main__':
    main()