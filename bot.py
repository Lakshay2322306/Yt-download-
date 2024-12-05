import logging
import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = 21438467  # Replace with your API ID
API_HASH = "320d16934ede2ce14fb4e1f0475e5e7e"  # Replace with your API Hash
BOT_TOKEN = "7180223394:AAEqekKqF7747OL6tx8jxjB0MRTpczhoxtY"  # Replace with your Bot Token

# Initialize Pyrogram Client
app = Client("youtube_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User data to store video URL and other information
user_data = {}

# Fetch YouTube thumbnail
def fetch_thumbnail(video_url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info["thumbnail"]
    except Exception as e:
        logger.error(f"Error fetching thumbnail: {e}")
        return None

# Download video or audio in selected quality
def download_media(video_url, quality):
    try:
        ydl_opts = {
            "format": quality,
            "outtmpl": "%(title)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None

# /start command handler
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("Welcome! Send me a YouTube link, and I'll fetch the thumbnail with download options!")

# YouTube link handler
@app.on_message(filters.text & ~filters.regex("^/"))
async def youtube_link_handler(client, message):
    video_url = message.text

    # Fetch thumbnail
    thumbnail_url = fetch_thumbnail(video_url)
    if thumbnail_url:
        # Save the video URL for the user
        user_data[message.chat.id] = {"video_url": video_url}

        # Inline buttons for quality selection
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("High", callback_data="High")],
            [InlineKeyboardButton("Medium", callback_data="Medium")],
            [InlineKeyboardButton("Low", callback_data="Low")],
            [InlineKeyboardButton("Audio Only", callback_data="Audio")],
        ])

        # Send thumbnail with quality options
        await message.reply_photo(
            photo=thumbnail_url,
            caption="Choose the download option:",
            reply_markup=buttons,
        )
    else:
        await message.reply_text("Failed to fetch video details. Please check the link.")

# Callback query handler for quality selection
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    quality = callback_query.data
    chat_id = callback_query.message.chat.id

    # Retrieve the video URL
    video_url = user_data.get(chat_id, {}).get("video_url")
    if not video_url:
        await callback_query.message.edit_text("Something went wrong. Please send the link again.")
        return

    # Notify user about the download process
    if quality == "Audio":
        await callback_query.message.edit_text("Downloading audio...")
        quality_format = "bestaudio/best"
    else:
        await callback_query.message.edit_text(f"Downloading video in {quality} quality...")
        quality_format = {
            "High": "bestvideo+bestaudio/best",
            "Medium": "best[height<=720]",
            "Low": "worst",
        }[quality]

    # Download video or audio
    media_file = download_media(video_url, quality_format)
    if media_file:
        if quality == "Audio":
            await client.send_audio(chat_id=chat_id, audio=media_file)
        else:
            await client.send_video(chat_id=chat_id, video=media_file)
        os.remove(media_file)  # Clean up the downloaded file
    else:
        await callback_query.message.edit_text("Failed to download. Please try again.")

# Run the bot
app.run()
