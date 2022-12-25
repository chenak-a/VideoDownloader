from downloader.VideoDownloader import  VideoDownloader
def main():
    downloader = VideoDownloader()
    downloader.downloadVideo("https://www.youtube.com/watch?v=WuHSBSLK3_A")
if __name__ == '__main__':
    main()