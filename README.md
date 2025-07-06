# Rust Base Twitter Bot

A Twitter bot that monitors YouTube channels for new Rust base design videos and automatically tweets about them.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the root directory with the following variables:

```bash
# YouTube API Configuration
YOUTUBE_API_KEY=your_youtube_api_key_here

# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_API_KEY=your_api_key_here
TWITTER_API_KEY_SECRET=your_api_key_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

4. Run the bot:
```bash
python main.py
```

## Features

- Monitors specified YouTube channels for new base design videos
- Filters videos based on base-related keywords
- Posts tweets with video thumbnails and information
- Skips videos shorter than 60 seconds
- Automatically cleans up temporary files

## Monitored Channels

- CrowRust
- FadedRust
- dustgg
- SecretBuilds
- spinky 