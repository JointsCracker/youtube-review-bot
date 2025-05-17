import requests
import json
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")
PLAYLIST_ID = os.getenv("YOUTUBE_PLAYLIST_ID")
SEEN_VIDEOS_FILE = "seen_videos.json"

def load_seen_video_ids():
    if os.path.exists(SEEN_VIDEOS_FILE):
        with open(SEEN_VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_seen_video_ids(video_ids):
    with open(SEEN_VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(video_ids, f, ensure_ascii=False, indent=2)

def fetch_latest_videos():
    url = (
        f"https://www.googleapis.com/youtube/v3/playlistItems"
        f"?part=snippet&playlistId={PLAYLIST_ID}&maxResults=50&key={API_KEY}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    videos = []
    for item in data.get("items", []):
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"id": video_id, "title": title, "url": url})
    return videos

def get_new_videos():
    seen_ids = load_seen_video_ids()
    current_videos = fetch_latest_videos()
    new_videos = [v for v in current_videos if v["id"] not in seen_ids]
    all_ids = [v["id"] for v in current_videos]
    save_seen_video_ids(all_ids)
    return new_videos
