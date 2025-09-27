import subprocess
import os

def process_requests(file_path, output_dir):
    if not os.path.exists(file_path):
        print(f"file {file_path} does not exists!")
        return
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "r+") as f:
        lines = f.readlines()
        print(lines)
        f.seek(0)
        f.truncate(0)

        if len(lines) != 0:
            for url in lines:
                url = url.strip()
                if isinstance(url, str) and 'youtu' in url:
                    print('valid url found, downloading...')
                    cmd = [
                        "./yt-dlp",  # path to the yt-dlp binary you downloaded
                        "-f", "140",
                        "--extract-audio",
                        "--audio-format", "mp3",
                        "--audio-quality", "192K",
                        "--add-metadata",
                        "--embed-thumbnail",
                        "--ffmpeg-location", "./ffmpeg",
                        "--ignore-errors",
                        "-o", f"{output_dir}/%(title)s.%(ext)s",
                        url]
                    try:
                        subprocess.run(cmd, check=True)
                    except Exception as e:
                        print(f"❌ Error downloading {url}: {e}")
                else:
                    print('invalid url found')
        else:
            print("No URLs to process.")


if __name__ == "__main__":
    REQUEST_FILE = "/mnt/Torrents/Plex_Media/shotcut.txt"
    LIBRARY_DIR = "/mnt/Torrents/Plex_Media/Movies/Music/downloaded"
    process_requests(REQUEST_FILE, LIBRARY_DIR)