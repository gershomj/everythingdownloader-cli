import os
import subprocess
import requests
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm
import yt_dlp as youtube_dl
from datetime import datetime
import pyfiglet
import keyboard


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
                if keyboard.is_pressed("esc"):  # Check for "Escape" key press
                    print("Skipping download...")
                    return
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


def download_music_spotify(url, save_folder):
    """Download music from Spotify using spotdl."""
    command = [
        'python3', '-m', 'spotdl', 'download', url,
        '--output', os.path.join(save_folder)
    ]

    # Run the command without capturing output
    result = subprocess.run(command)

    # Check the return code
    if result.returncode != 0:
        print("Error downloading from Spotify.")
    else:
        print(f"Downloaded song from {url} to {save_folder}")


def detect_file_type(url):
    """Detect the file type based on URL."""
    if url.startswith('https://open.spotify.com/track/'):
        return 'spotify_track'
    elif url.startswith('https://open.spotify.com/playlist/'):
        return 'spotify_playlist'
    elif 'youtube.com/watch' in url or 'youtu.be' in url or 'youtube.com/shorts' in url:
        return 'youtube_video'
    elif 'youtube.com/playlist' in url:
        return 'youtube_playlist'
    elif url.startswith('http'):
        return 'website'
    return 'unknown'  # Default to 'unknown' for any unrecognized file types


def download_file_with_check(url, save_folder, downloaded_files):
    """Downloads a file if it hasn't been downloaded already."""
    file_type = detect_file_type(url)

    if file_type == 'spotify_track':
        download_music_spotify(url, save_folder)  # Pass save_folder here
    elif file_type == 'spotify_playlist':
        download_music_spotify(url, save_folder)  # You might want to create a separate function for playlists if needed
    elif file_type == 'youtube_video':
        download_video(url, save_folder)
    elif file_type == 'youtube_playlist':
        download_youtube_playlist(url, save_folder, downloaded_files)
    elif file_type == 'website':
        download_webpage(url, save_folder)
    else:
        print(f"❓ Unrecognized file type for URL: {url}")


def load_urls_from_file(file_path):
    """Loads URLs from a CSV or text file into an array."""
    urls = []
    if file_path.endswith('.csv'):
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:  # Skip empty rows
                    urls.append(row[0])  # Assuming each row contains only the URL
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as txtfile:
            urls = [line.strip() for line in txtfile.readlines()]
    return urls


def main():
    ascii_banner = pyfiglet.figlet_format("Download Everything")
    print(ascii_banner)

    save_folder = input("Enter the folder to save downloaded files: ")
    
    # Create folder if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Ask if user wants to load URLs from a file
    load_from_file = input("Do you want to load URLs from a file? (yes/no): ").strip().lower()
    
    urls = []
    if load_from_file == 'yes':
        file_path = input("Enter the path to the file (CSV or TXT): ").strip()
        try:
            urls = load_urls_from_file(file_path)
            print(f"✅ Loaded {len(urls)} URLs from {file_path}")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return
    else:
        # Get URLs from the user
        while True:
            url = input("Enter URL to download (or type 'done' to finish): ")
            if url.lower() == 'done':
                break
            urls.append(url)

    downloaded_files = set()  # Track downloaded files to avoid duplicates

    # Process each URL based on its type without prompting
    for url in urls:
        download_file_with_check(url, save_folder, downloaded_files)

    # After all downloads
    print("Download operations completed!")


if __name__ == '__main__':
    main()
