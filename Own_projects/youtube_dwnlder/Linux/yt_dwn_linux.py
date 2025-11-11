import subprocess
import os

def process_requests(file_path):
    with open(file_path, "r+",encoding='utf-8') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate(0)
        if len(lines) != 0:
            for url in lines:
                url = url.strip()
                if isinstance(url, str) and 'youtu' in url:
                    print('valid url found, downloading...')
                    download_youtube_link(file_path,yd_dwnlr_tool,download_folder,url,ff_mpeg_codec)
                else:
                    print('invalid url found')
        else:
            print("No URLs to process.")

def download_youtube_link(file_path,ytdlp_tool,output_dir,url,ff_mpeg_codec):
    if not os.path.exists(file_path):
        print(f"shotcut file: {file_path} does not exists!")
        return
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        ytdlp_tool,  # path to the yt-dlp binary you downloaded
        "-f", "140",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "192K",
        "--add-metadata",
        "--embed-thumbnail",
        "--ffmpeg-location", ff_mpeg_codec,
        "--ignore-errors",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        url]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

if __name__ == "__main__":
    ff_mpeg_codec = "/mnt/Torrents/Plex_Media/youtube/ffmpeg"
    yd_dwnlr_tool = "/mnt/Torrents/Plex_Media/youtube/yt-dlp"
    shotcut_txtfile = "/mnt/Torrents/Plex_Media/shotcut.txt"
    download_folder = "/mnt/Torrents/Plex_Media/Movies/Music/downloaded"
    process_requests(shotcut_txtfile)