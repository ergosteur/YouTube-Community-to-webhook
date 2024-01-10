#!/usr/bin/env python3
# Python script for crossposting YouTube Community posts to a Discord channel.
# Uses https://github.com/Benjamin-Loison/YouTube-operational-API to fetch the Community Posts since YouTube's Data V3 API is useless for this
# I would recommend using your instance of the YouTube-operational-API to avoid any issues.
#
# Edit the variables in the main() function as needed, and the api_url in the fetch_youtube_content function.

import requests
import time
import datetime
import os
import re

# Fetch content from a YouTube channel's Community tab using the custom API
def fetch_youtube_content(channel_id):
    api_url = f"https://ergosteur.com/apis/YouTube-operational-API/channels?part=community&id={channel_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

# Get Channel name and icon from Channel ID using Official YouTube Data API (requires API Key)
def get_channel_info(channel_id, api_key):
    api_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={api_key}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            channel_info = data["items"][0]["snippet"]
            channel_name = channel_info["title"]
            channel_icon_url = channel_info.get("thumbnails", {}).get("default", {}).get("url", "")
            return channel_name, channel_icon_url
    return "Unknown Channel", ""

# Extract text, image URL, and other details from the API response
def extract_content(post_data, youtube_channel_url):
    post_id = post_data.get("id", "")
    print(f"Got Community post: {post_id}")
    post_url = f"https://www.youtube.com/post/{post_id}" if post_id else youtube_channel_url

    # Concatenate all text segments and links
    full_text = ''
    for text_part in post_data.get("contentText", []):
        full_text += text_part.get("text", '')
    # Get post date
    date = post_data.get("date", "Unknown")
    # Check if there are any images, and get the largest thumbnail if available
    image_url = ""
    if post_data.get("images"):
        image_url = post_data.get("images", [{}])[0].get("thumbnails", [{}])[-1].get("url", "")

    # Build json for Discord Webhook
    content = {
        "text": full_text.strip(),
        "image_url": image_url,
        "published_at": date,
        "title": "YouTube Community Post",
        "url": post_url
    }
    return content

# Log posted urls to file
def log_post_url(url, url_log):
    with open(url_log, "a") as file:
        file.write(url + "\n")

# Check if url is in posted log
def is_posted(url, url_log):
    try:
        with open(url_log, "r") as file:
            posted_urls = file.read().splitlines()
        return url in posted_urls
    except FileNotFoundError:
        return False

# Post content to Discord via Webhook with the specified template and return the response status code
def post_to_discord(webhook_url, channel_name, channel_icon_url, content, mention, retry_count=0):
    max_retries = 3
    # Determine the mention text based on the variables from main
    mention_text = f"@{mention} " if mention != "none" else ""
    discord_data = {
        "content": mention_text + "new community post!",
        "embeds": [{
            "color": 16711680,
            "author": {
                "name": channel_name,
                "icon_url": channel_icon_url
            },
            "title": content["title"],
            "url": content["url"],
            "description": content["text"],
            "image": {"url": content["image_url"]},
            "footer": {"text": "Published: " + content["published_at"]}
        }]
    }

    # Log the data being sent
    print("Sending data to Discord:", discord_data)

    response = requests.post(webhook_url, json=discord_data)
    if response.status_code == 429 and retry_count < max_retries:
        # Extract the retry_after value from the response
        retry_after = response.json().get("retry_after", 1)  # Default to 1 second if not provided
        print(f"Rate limited by Discord. Retrying after {retry_after} seconds (Retry {retry_count + 1}/{max_retries}).")
        time.sleep(retry_after)  # Wait before retrying
        return post_to_discord(webhook_url, channel_name, channel_icon_url, content, mention, retry_count + 1)  # Retry posting with incremented retry count
    elif response.status_code not in range(200, 300):
        print("Error:", response.status_code, response.text)

    return response.status_code

# Functions to fetch prior urls list via http (for docker deployment)
def fetch_and_validate_url_list(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        urls = response.text.splitlines()
        valid_urls = [url for url in urls if 'youtube.com' in url]
        return valid_urls
    except Exception as e:
        print(f"Error fetching or validating URL list: {e}")
        return []

def initialize_posted_urls_log(posted_urls_log_path, url_list):
    with open(posted_urls_log_path, 'w') as file:
        for url in url_list:
            file.write(url + '\n')


# Main function
def main():
    ## VARIABLES TO DEFINE BEFORE USE IF NOT USING DOCKER ##
    max_posts = int(os.getenv('MAX_POSTS', 10))  # 0 for all posts, > 0 for specific number # Select whether to send all available community posts to the webhook
    channel_id = os.getenv('CHANNEL_ID', 'UCE6acMV3m35znLcf0JGNn7Q')  # YouTube channel ID
    mention = os.getenv('MENTION', "none")  # Set role to mention (everyone, here, none)
    api_key = api_key = os.getenv('API_KEY') # YouTube API Key from Google Developer console
    webhook_url = webhook_url = os.getenv('WEBHOOK_URL') # Discord webhook URL
    ignorelist_url = os.getenv('POST_IGNORELIST_URL') # URL for list of community post urls to ignore
    ## END VARIABLES CONFIG ##

    script_directory = os.path.dirname(os.path.realpath(__file__)) # Get the directory where the script is located
    data_directory = os.path.join(script_directory, 'data') # Path to the data directory
    # Create the data directory if it doesn't exist
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    url_log_file = os.path.join(data_directory, 'posted_urls.log') # Define file for logging posted urls

    youtube_channel_url = f"https://www.youtube.com/channel/{channel_id}"
    channel_name, channel_icon_url = get_channel_info(channel_id, api_key)  # Get the channel name and icon

    print("Script run started at ", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Create the initial url_log_file from fetched list if it doesn't exist
    if not os.path.exists(url_log_file):
        if ignorelist_url:
            url_list = fetch_and_validate_url_list(ignorelist_url)
            if url_list:
                initialize_posted_urls_log(url_log_file, url_list)
        else:
            print("Ignorelist URL not provided. Skipping initialization.")

    youtube_content = fetch_youtube_content(channel_id)
    if youtube_content and "items" in youtube_content:
        for item in youtube_content["items"]:
            community_posts = item.get("community", [])
            total_num_posts = len(community_posts)

            # Reverse the order of the posts for chronological posting if processing all posts
            if max_posts == 0 or max_posts > total_num_posts:
                community_posts = list(reversed(community_posts)) # convert reverseiterator to list
            # if max_posts is not unlimited, slice list before reversing to keep most recent
            elif max_posts > 0:
                community_posts = community_posts[:max_posts]
                community_posts = list(reversed(community_posts)) # convert reverseiterator to list
            elif max_posts < 0 :
                print(f"Invalid value {max_posts} for max_posts")
            print(f"Sending {len(community_posts)}/{total_num_posts} most recent community posts to webhook")

            for post in community_posts:
                content = extract_content(post, youtube_channel_url)
                if content and not is_posted(content["url"], url_log_file):
                    response = post_to_discord(webhook_url, channel_name, channel_icon_url, content, mention)
                    if response in range(200, 300):
                        log_post_url(content["url"], url_log_file)
                    print(f"{content['url']} posted to Discord with status code: {response}")
                elif content and is_posted(content["url"], url_log_file):
                    print(f"{content['url']} already posted to Discord")

    print("Script run ended at ", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()

