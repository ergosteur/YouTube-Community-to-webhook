# YouTube-Community-to-webhook
Python script for crossposting YouTube Community posts to a Discord channel via webhook.
Uses https://github.com/Benjamin-Loison/YouTube-operational-API to fetch the Community Posts since YouTube's Data V3 API is useless for this
I would recommend using your instance of the YouTube-operational-API to avoid any issues. The one in the script may be disabled at any moment.
 
Edit the variables in the main() function as needed, and the api_url in the fetch_youtube_content function.

Coded with assistance from ChatGPT 4

Script would need to be scheduled to run via cron or something, currently nothing is implemented to detect a new community post.