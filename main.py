# Funktioner
# 1. Alert that checks if YouTuber uploaded a new base video
# 1.1 Extract the Creator name, base name and YouTube thumbnail
# 2. Tweet about the new base

import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import tweepy
import requests
import os

# YouTube API Configuration
youtubeDeveloperKey = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=youtubeDeveloperKey)

# Tweety API Configuration
clientID = os.getenv('TWITTER_CLIENT_ID')
clientSecret = os.getenv('TWITTER_CLIENT_SECRET')
apiKey = os.getenv('TWITTER_API_KEY')
apiKeySecret = os.getenv('TWITTER_API_KEY_SECRET')
bearerToken = os.getenv('TWITTER_BEARER_TOKEN')
accessToken = os.getenv('TWITTER_ACCESS_TOKEN')
accessTokenSecret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
client = tweepy.Client(bearerToken, apiKey, apiKeySecret, accessToken, accessTokenSecret)
auth = tweepy.OAuth1UserHandler(apiKey, apiKeySecret, accessToken, accessTokenSecret)
api = tweepy.API(auth)

# List of YouTube Channel IDs to monitor [ CrowRust, FadedRust., dustgg, SecretBuilds]
channel_ids = ["UCnuk6QPjyRA_SCE4I6RcPbA", "UCaDoxfzWNonZY0_dQbE1VcQ", "UCCD4iiHMnIbbOO-x7xlrfwQ", "UCggN2nAvCu2JbTSTm-FkqdA"]


# Function to fetch the latest video
def get_latest_video(channel_id):
    try:
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            order='date',
            maxResults=1
        )
        response = request.execute()

        if response['items']:
            latest_video = response['items'][0]
            return {
                'title': latest_video['snippet']['title'],
                'video_id': latest_video['id']['videoId'],
                'published_at': latest_video['snippet']['publishedAt'],
                'thumbnail_url': latest_video['snippet']['thumbnails']['high']['url'],
                'channel_title': latest_video['snippet']['channelTitle']
            }
        return None
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None

# Function to download the thumbnail image
def download_thumbnail(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)

# Function to tweet the new video
def tweet_video(video):
    try:
        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        tweet_text = (f"New base design by {video['channel_title']}.\n\n"
                      f"\"{video['title']}\"\n\n"
                      f"Check it out here: {video_url}\n\n"
                      f"#rustbasedesign #playrust #RustGame #RustCommunity")
        thumbnail_filename = 'thumbnail.jpg'
        download_thumbnail(video['thumbnail_url'], thumbnail_filename)
        media = api.media_upload(thumbnail_filename)
        media_list = [media.media_id]
        client.create_tweet(text=tweet_text, media_ids=media_list)
        print(f"Tweeted: {tweet_text}")
        os.remove(thumbnail_filename)  # Clean up the thumbnail file
    except Exception as e:
        print(f"An error occurred while tweeting: {e}")


# Load the last video ID for a specific channel from file
def load_last_video_id(channel_id):
    try:
        with open(f'last_video_id_{channel_id}.json', 'r') as file:
            data = json.load(file)
            return data.get('video_id')
    except FileNotFoundError:
        return None

# Save the last video ID for a specific channel to file
def save_last_video_id(channel_id, video_id):
    with open(f'last_video_id_{channel_id}.json', 'w') as file:
        json.dump({'video_id': video_id}, file)

def main():
    while True:
        for channel_id in channel_ids:
            latest_video = get_latest_video(channel_id)
            if latest_video:
                last_video_id = load_last_video_id(channel_id)
                if latest_video['video_id'] != last_video_id:
                    print("new video found")
                    tweet_video(latest_video)
                    save_last_video_id(channel_id, latest_video['video_id'])
                else:
                    print("no new video")
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
