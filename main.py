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
import isodate
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# YouTube API Configuration
youtubeDeveloperKey = os.getenv('YOUTUBE_API_KEY')
if not youtubeDeveloperKey:
    raise ValueError("YouTube API key not found in environment variables")

youtube = build(
    'youtube', 
    'v3', 
    developerKey=youtubeDeveloperKey,
    static_discovery=False
)

# Twitter API Configuration
twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
twitter_api_key = os.getenv('TWITTER_API_KEY')
twitter_api_key_secret = os.getenv('TWITTER_API_KEY_SECRET')
twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Verify Twitter credentials are present
if not all([twitter_bearer_token, twitter_api_key, twitter_api_key_secret, 
            twitter_access_token, twitter_access_token_secret]):
    raise ValueError("One or more Twitter API credentials not found in environment variables")

client = tweepy.Client(
    bearer_token=twitter_bearer_token,
    consumer_key=twitter_api_key,
    consumer_secret=twitter_api_key_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

# For media upload functionality
auth = tweepy.OAuth1UserHandler(
    consumer_key=twitter_api_key,
    consumer_secret=twitter_api_key_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)
api = tweepy.API(auth)

# List of YouTube Channel IDs to monitor [ CrowRust, FadedRust., dustgg, SecretBuilds, spinky]
channel_ids = ["UCnuk6QPjyRA_SCE4I6RcPbA", "UCaDoxfzWNonZY0_dQbE1VcQ", "UCCD4iiHMnIbbOO-x7xlrfwQ", "UCggN2nAvCu2JbTSTm-FkqdA", "UCOPeeimwxtWjRDgim96Sxlg"]

# Function to check if video title is related to base designs
def is_base_video(title):
    """
    Check if a video title is related to base designs.
    Returns False for videos about patches, updates, or other non-base content.
    """
    # Convert title to lowercase for case-insensitive matching
    title_lower = title.lower()
    
    # Keywords that indicate it's NOT a base design video
    negative_keywords = [
        'patch',
        'update',
        'getting patched',
        'exploit',
        'glitch',
        'bug',
        'fixed',
        'fixing',
        'tc exploit',
        'external tc',
        'raid',
        'raiding',
        'online raid',
        'offline raid',
        'vs',
        'versus',
        'fight',
        'pvp',
        'play wipe',
        'playing wipe',
        'highlights'
    ]
    
    # If any negative keyword is found, it's not a base video
    if any(keyword in title_lower for keyword in negative_keywords):
        print(f"Skipped due to negative keyword match: {title}")
        return False
    
    # Single keywords that directly indicate a base design video
    direct_keywords = [
        'base design',
        'base build',
        'building 3.',
        'building 2.',
        'building a',
        'bunker base',
        'compound design',
        'starter base',
        'main base'
    ]
    
    # Compound keywords - must have both parts to qualify
    compound_keywords = [
        ('solo', 'base'),
        ('duo', 'base'),
        ('trio', 'base'),
        ('solo', 'bunker'),
        ('duo', 'bunker'),
        ('trio', 'bunker'),
        ('weekly', 'base'),
        ('monthly', 'base'),
        ('clan', 'base'),
        ('group', 'base'),
        ('cheap', 'base'),
        ('strong', 'base'),
        ('best', 'base')
    ]
    
    # Check direct keywords first - these are most reliable
    if any(keyword in title_lower for keyword in direct_keywords):
        return True
        
    # Check compound keywords - both parts must be present
    if any(all(part in title_lower for part in pair) for pair in compound_keywords):
        return True
        
    # Special case for "solo/duo" and "duo/trio" formats
    special_formats = ['solo/duo', 'duo/trio']
    if any(format in title_lower for format in special_formats):
        # Only return True if 'base' or 'bunker' is also in the title
        return any(base_word in title_lower for base_word in ['base', 'bunker'])
    
    # If none of the positive patterns matched, it's not a base video
    print(f"Skipped: No base design keywords found in title: {title}")
    return False

# Function to fetch the latest video
def get_latest_video(channel_id):
    try:
        # Search for the latest video on the channel
        search_request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            order='date',
            maxResults=1
        )
        search_response = search_request.execute()

        if search_response['items']:
            latest_video = search_response['items'][0]
            video_title = latest_video['snippet']['title']

            # First check if it's a base-related video
            if not is_base_video(video_title):
                print(f"Skipped non-base video: {video_title}")
                return None

            # Retrieve the video ID
            video_id = latest_video['id']['videoId']

            # Get additional details about the video, including duration
            video_request = youtube.videos().list(
                part='contentDetails',
                id=video_id
            )
            video_response = video_request.execute()

            if video_response['items']:
                video_details = video_response['items'][0]
                duration = video_details['contentDetails']['duration']

                # Parse the duration
                duration_in_seconds = isodate.parse_duration(duration).total_seconds()

                # Check if the video is longer than 60 seconds
                if 60 < duration_in_seconds <= 3600:
                    return {
                        'title': video_title,
                        'video_id': video_id,
                        'published_at': latest_video['snippet']['publishedAt'],
                        'thumbnail_url': latest_video['snippet']['thumbnails']['high']['url'],
                        'channel_title': latest_video['snippet']['channelTitle']
                    }
                else:
                    print(f"Skipped video due to duration: {video_title}")
                    return None
        return None
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None

# Function to download the thumbnail image
def download_thumbnail(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)

# Function to get tweet ID from response
def get_tweet_id(response):
    """Extract tweet ID from response, handling different tweepy versions"""
    if isinstance(response, tuple):
        return response[0]['id']
    if hasattr(response, 'data') and isinstance(response.data, dict):
        return response.data.get('id')
    if hasattr(response, 'id'):
        return response.id
    return None

# Function to tweet the new video
def tweet_video(video):
    try:
        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        tweet_text = (f"New base design by {video['channel_title']}.\n\n"
                      f"\"{video['title']}\"\n\n"
                      f"Check it out here: {video_url}\n\n"
                      f"#rustbasedesign #playrust #RustGame #RustCommunity")
        
        # Download and upload the thumbnail
        thumbnail_filename = 'thumbnail.jpg'
        download_thumbnail(video['thumbnail_url'], thumbnail_filename)
        
        try:
            # Upload media
            media = api.media_upload(thumbnail_filename)
            
            # Create tweet with media
            response = client.create_tweet(
                text=tweet_text,
                media_ids=[media.media_id]
            )
            
            tweet_id = get_tweet_id(response)
            if tweet_id:
                print(f"Tweet created successfully! Tweet ID: {tweet_id}")
            else:
                print("Tweet created successfully! (ID unknown)")
            
        finally:
            # Clean up the thumbnail file
            if os.path.exists(thumbnail_filename):
                os.remove(thumbnail_filename)
                
    except Exception as e:
        print(f"An error occurred while tweeting: {e}")
        raise  # Re-raise the exception for proper error handling


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

# Function to test APIs
def test_apis():
    print("Testing YouTube API...")
    try:
        # Test YouTube API by fetching latest video from one channel
        channel_id = "UCnuk6QPjyRA_SCE4I6RcPbA"  # CrowRust's channel
        latest_video = get_latest_video(channel_id)
        if latest_video:
            print("✓ YouTube API working! Found video:", latest_video['title'])
        else:
            print("× YouTube API test failed: No video found")
    except Exception as e:
        print(f"× YouTube API test failed: {str(e)}")

    print("\nTesting Twitter API...")
    try:
        # Test Twitter API by posting a test tweet with an image
        test_image_url = "https://i.imgur.com/8bHZfRy.jpg"  # Example Rust game image
        download_thumbnail(test_image_url, 'test_thumbnail.jpg')
        
        try:
            # Upload test image
            media = api.media_upload('test_thumbnail.jpg')
            
            # Post test tweet
            response = client.create_tweet(
                text="🤖 Test tweet from Rust Base Bot!\n\nThis is a test of the Twitter API. If you see this, the bot is working correctly!\n\n#RustGame #TestTweet",
                media_ids=[media.media_id]
            )
            
            tweet_id = get_tweet_id(response)
            if tweet_id:
                print(f"✓ Twitter API working! Tweet posted with ID: {tweet_id}")
            else:
                print("✓ Twitter API working! Tweet posted (ID unknown)")
            
        finally:
            # Clean up test image
            if os.path.exists('test_thumbnail.jpg'):
                os.remove('test_thumbnail.jpg')
    except Exception as e:
        print(f"× Twitter API test failed: {str(e)}")

if __name__ == "__main__":
    test_apis()  # Run tests first
    print("\nStarting main bot loop...")
    main()  # Then start the main bot loop
