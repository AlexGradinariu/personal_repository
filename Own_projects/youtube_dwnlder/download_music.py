import os
import yt_dlp



def download_youtube_mp3(url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def process_requests(file_path):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate(0)

        if len(lines) != 0:
            for url in lines:
                url = url.strip()
                if isinstance(url, str) and 'youtu' in url:
                    print('valid url found, downloading...')
                    try:
                        download_youtube_mp3(url, LIBRARY_DIR)
                    except Exception as e:
                        print(f"❌ Error downloading {url}: {e}")
                else:
                    print('invalid url found')
        else:
            print("No URLs to process.")

if __name__ == "__main__":
    REQUEST_FILE = r"E:\test.txt"
    LIBRARY_DIR = r"E:\youtube_music"
    process_requests(REQUEST_FILE)
