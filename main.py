from downloader import VideoDownloader


def main():
    downloader = VideoDownloader()
    video = [
        "https://www.youtube.com/watch?v=IUWJ8_lkFAA",
        "https://www.youtube.com/watch?v=G8h_2bvkHa0",
        "https://www.youtube.com/watch?v=F9Zt4IFOvLI",
    ]
    audio = [
        "https://www.youtube.com/watch?v=BYRsQvPOv6o",
        ]
    
    downloader.run(video=video, audio=audio)


if __name__ == "__main__":
    main()
