import os
import subprocess
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import yt_dlp as youtube_dl
from datetime import datetime

def prompt_user(question, default='yes'):
    valid_responses = {'yes': True, 'y': True, 'no': False, 'n': False}
    while True:
        response = input(f"{question} [{'Y/n' if default == 'yes' else 'y/N'}]: ").lower()
        if response == '' and default:
            return valid_responses[default]
        if response in valid_responses:
            return valid_responses[response]
        print("Please answer with 'yes' or 'no'.")

def download_file(url, output_dir):
    local_filename = os.path.join(output_dir, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        block_size = 1024
        with open(local_filename, 'wb') as f, tqdm(
            total=total_size, unit='iB', unit_scale=True
        ) as bar:
            for chunk in r.iter_content(chunk_size=block_size):
                bar.update(len(chunk))
                f.write(chunk)
    print(f"Downloaded file to {local_filename}")

def download_webpage(url, output_dir):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string if soup.title else "webpage"
        file_path = os.path.join(output_dir, f"{page_title}.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Downloaded web page to {file_path}")
    else:
        print("Failed to download web page.")

def download_video(url, output_dir):
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded video from {url} in highest quality.")

def download_music_spotify(url, output_dir, is_playlist=False):
    if is_playlist:
        playlist_name = "My Playlist"  # Placeholder for playlist name extraction
        output_path = os.path.join(output_dir, f"{playlist_name}.%(ext)s")
    else:
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(output_dir, f"{current_date}.%(ext)s")

    command = [
        'python3', '-m', 'spotdl', 'download', url,
        '--output', output_path
    ]

    # Run the command without capturing output
    result = subprocess.run(command)

    # Check the return code
    if result.returncode != 0:
        print("Error downloading from Spotify.")
    else:
        if is_playlist:
            print(f"Downloaded playlist from {url} as '{playlist_name}.ext'.")
        else:
            print(f"Downloaded song from {url} as '{current_date}.ext'.")

def smart_download(url, output_dir):
    if 'youtube.com' in url or 'youtu.be' in url:
        confirm = prompt_user("This looks like a YouTube video. Download video?", 'yes')
        if confirm:
            download_video(url, output_dir)
    elif 'spotify.com' in url:
        confirm = prompt_user("This looks like a Spotify link. Is this a playlist?", 'no')
        if confirm:
            download_music_spotify(url, output_dir, is_playlist=True)
        else:
            download_music_spotify(url, output_dir)
    elif url.endswith(('html', 'htm')):
        confirm = prompt_user("This looks like a web page. Download as web page?", 'yes')
        if confirm:
            download_webpage(url, output_dir)
    else:
        confirm = prompt_user("Download this as a file?", 'yes')
        if confirm:
            download_file(url, output_dir)

def main():
    parser = argparse.ArgumentParser(description='Smart downloader for files, videos, music, websites.')
    parser.add_argument('--url', required=True, help='The URL to download from.')
    parser.add_argument('--output', default='downloads', help='The output directory to save the downloaded content.')
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    smart_download(args.url, args.output)

if __name__ == '__main__':
    main()
