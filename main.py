from downloader import VideoDownloader , Format
def main():
    type = Format()
    downloader = VideoDownloader()
    video = ["https://www.youtube.com/watch?v=cnKs1MiYQmE"]
    for i in video:
        downloader.downloadVideo(i,type.AUDIO)
if __name__ == '__main__':
    main()