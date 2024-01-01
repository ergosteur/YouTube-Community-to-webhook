#!/usr/bin/env python3
# Python script for crossposting YouTube Community posts to a Discord channel.
# Uses https://github.com/Benjamin-Loison/YouTube-operational-API to fetch the Community Posts since YouTube's Data V3 API is useless for this
# I would recommend using your instance of the YouTube-operational-API to avoid any issues.
# 
# Edit the variables in the main() function as needed, and the api_url in the fetch_youtube_content function.

import requests

# Fetch content from a YouTube channel's Community tab using the custom API
def fetch_youtube_content(channel_id):
    api_url = f"https://ergosteur.com/apis/YouTube-operational-API/channels?part=community&id={channel_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

# Extract text, image URL, and other details from the API response
def extract_content(post_data, youtube_channel_url):
    post_id = post_data.get("id", "")
    print(post_id)
    post_url = f"https://www.youtube.com/post/{post_id}" if post_id else youtube_channel_url

    # Concatenate text segments and links
    full_text = ''
    for text_part in post_data.get("contentText", []):
        #if "url" in text_part:
        #    # Append both the text and the URL for link segments
        #    full_text += text_part.get("text", '') + " (" + text_part.get("url", '') + ") "
        #else:
        #    # Append just the text for regular text segments
        #    full_text += text_part.get("text", '')
        full_text += text_part.get("text", '')
        #print(f"Text so far: {full_text}")

    date = post_data.get("date", "Unknown")
    image_url = post_data.get("images", [{}])[0].get("thumbnails", [{}])[-1].get("url", "")

    content = {
        "text": full_text.strip(),
        "image_url": image_url,
        "published_at": date,
        "title": "New Community Post",
        "url": post_url
    }
    return content



# Log posted urls to file
def log_post_url(url, log_file="posted_urls.log"):
    with open(log_file, "a") as file:
        file.write(url + "\n")

def is_posted(url, log_file="posted_urls.log"):
    try:
        with open(log_file, "r") as file:
            posted_urls = file.read().splitlines()
        return url in posted_urls
    except FileNotFoundError:
        return False

# Post content to Discord via Webhook with the specified template
def post_to_discord(webhook_url, channel_name, content):
    discord_data = {
        "embeds": [{
            "color": 16711680,
            "author": {
                "name": channel_name,
                "icon_url": content.get("icon_url", "")
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
    if response.status_code not in range(200,300):
        print("Error:", response.status_code, response.text)
    return response.status_code

# Main function
def main():
    channel_id = 'UCE6acMV3m35znLcf0JGNn7Q'  # Example channel ID
    youtube_channel_url = f"https://www.youtube.com/channel/{channel_id}"
    webhook_url = 'DISCORD_WEBHOOK_URL' # Replace with your Discord webhook URL
    channel_name = 'Gibi ASMR'  # Set the channel name
    all_posts = True # Select whether to send all available community posts to the webhook

    youtube_content = fetch_youtube_content(channel_id)
    if youtube_content and "items" in youtube_content:
        for item in youtube_content["items"]:
            community_posts = item.get("community", [])
            
            # Reverse the order of the posts for chronological posting if all_posts is True
            if all_posts:
                community_posts = reversed(community_posts)

            for post in community_posts:
                content = extract_content(post, youtube_channel_url)
                if content and not is_posted(content["url"]):
                    response = post_to_discord(webhook_url, channel_name, content)
                    if response in range(200, 300):
                        log_post_url(content["url"])
                    print(f"Posted to Discord with status code: {response}")

                if not all_posts:
                    break  # Breaks the inner loop, stops after the first (most recent) post
            if not all_posts:
                break  # Breaks the outer loop if only the latest post is needed

if __name__ == "__main__":
    main()

