#!/usr/bin/env python3
import requests

# Fetch content from a YouTube channel's Community tab using the custom API
def fetch_youtube_content(channel_id):
    api_url = f"https://yt.lemnoslife.com/channels?part=community&id={channel_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

# Extract text, image URL, and other details from the API response
def extract_content(post_data, youtube_channel_url):
    # Extracting the post ID for URL construction
    post_id = post_data.get("id", "")
    post_url = f"https://www.youtube.com/post/{post_id}" if post_id else youtube_channel_url

    # Extracting content from the post
    text = post_data.get("contentText", [{}])[0].get("text", "")
    date = post_data.get("date", "Unknown")
    image_url = post_data.get("images", [{}])[0].get("thumbnails", [{}])[-1].get("url", "")  # Get the largest thumbnail

    content = {
        "text": text,
        "image_url": image_url,
        "published_at": date,
        "title": "New Community Post",
        "url": post_url  # Use the constructed post URL
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
    webhook_url = 'https://discord.com/api/webhooks/1191138143613759528/xZBJJaFo03vIEGzz5DuWu2Kted6e4np75PrIElpYtvA9xP83JySaWxwvs0-ZC1MHuMp_'
    channel_name = 'Gibi ASMR'  # Set the channel name
    all_posts = True # Select whether to send all available community posts to the webhook

    youtube_content = fetch_youtube_content(channel_id)
    if youtube_content and "items" in youtube_content:
        for item in youtube_content["items"]:
            # Check if there are multiple posts in the community item
            for post in item.get("community", []):
                content = extract_content(post, youtube_channel_url)
                if content and not is_posted(content["url"]):
                    response = post_to_discord(webhook_url, channel_name, content)
                    if response in range(200, 300):
                        log_post_url(content["url"])
                    print(f"Posted to Discord with status code: {response}")

                if not all_posts:
                    break  # Breaks the inner loop, continue for the outer loop
            if not all_posts:
                break  # Breaks the outer loop if only the latest post is needed


if __name__ == "__main__":
    main()

