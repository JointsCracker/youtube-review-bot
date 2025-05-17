import os
import json
import requests
from monitor_playlist import get_new_videos
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api._errors import RequestBlocked
from bs4 import BeautifulSoup
import random
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_proxy_list():
    url = "https://free-proxy-list.net/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    proxy_list = []

    for row in soup.select("table#proxylisttable tbody tr"):
        cols = row.find_all("td")
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        https = cols[6].text.strip()
        if https == "yes":
            proxy_list.append(f"http://{ip}:{port}")
    return proxy_list

def get_transcript(video_id, max_tries=10):
    proxies = get_proxy_list()
    random.shuffle(proxies)

    for i, proxy in enumerate(proxies[:max_tries]):
        print(f"🔁 Trying proxy {i+1}/{max_tries}: {proxy}")
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id, proxies={"http": proxy, "https": proxy})

            if transcripts.find_manually_created_transcript(['en', 'ar']):
                transcript = transcripts.find_manually_created_transcript(['en', 'ar'])
            else:
                transcript = transcripts.find_generated_transcript(['en', 'ar'])

            text = " ".join([entry['text'] for entry in transcript.fetch()])
            print("✅ Transcript retrieved successfully.")
            return text

        except RequestBlocked:
            print("❌ Proxy blocked. Trying next...")
        except (TranscriptsDisabled, NoTranscriptFound):
            print("⚠️ Transcript not available.")
            return None
        except Exception as e:
            print(f"⚠️ Unexpected error with proxy {proxy}: {e}")
    print("❌ All proxies failed.")
    return None

def transcribe_with_whisper(video_url):
    return f"Transcribed text from Whisper for video: {video_url}"

def summarize_text(text, language="en"):
    prompt = f"Summarize the following text in {language}:\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    return requests.post(url, data=data).ok

def is_arabic(text):
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return arabic_chars > 10

def main():
    new_videos = get_new_videos()
    if not new_videos:
        print("No new videos found.")
        return

    for video in new_videos:
        video_id = video['id']
        video_url = video['url']
        video_title = video['title']

        print(f"📺 Processing video: {video_title}")

        transcript = get_transcript(video_id)
        if not transcript:
            print("🧠 No transcript found, using Whisper...")
            transcript = transcribe_with_whisper(video_url)

        lang = "ar" if is_arabic(transcript) else "en"
        summary = summarize_text(transcript, lang)

        message = f"<b>{video_title}</b>\n\nSummary ({lang}):\n{summary}\n\n{video_url}"
        sent = send_telegram_message(message)

        if sent:
            print(f"✅ Sent to Telegram: {video_title}")
        else:
            print(f"❌ Failed to send Telegram message for: {video_title}")

if __name__ == "__main__":
    main()
