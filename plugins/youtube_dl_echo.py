import logging
import asyncio
import json
from config import Config
from pyrogram import filters
from database.access import clinton
from translation import Translation
from database.adduser import AddUser
from pyrogram import Client
from helper_funcs.display_progress import humanbytes
from helper_funcs.help_uploadbot import DownLoadFile
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter

# Import bot client from bot.py
from bot import Warrior  

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

@Warrior.on_message(filters.private & ~filters.via_bot & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    await AddUser(bot, update)

    imog = await update.reply_text("Processing...⚡", reply_to_message_id=update.id)

    url = update.text.strip()
    file_name = None
    youtube_dl_username = None
    youtube_dl_password = None

    # Extract URL and filename if provided
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url, file_name = url_parts
        elif len(url_parts) == 4:
            url, file_name, youtube_dl_username, youtube_dl_password = url_parts
    else:
        for entity in update.entities or []:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                url = update.text[entity.offset : entity.offset + entity.length]

    if not url:
        await imog.edit_text("Invalid URL! Please send a valid link.")
        return

    # Prepare yt-dlp command
    command_to_exec = ["yt-dlp", "--no-warnings", "--youtube-skip-dash-manifest", "-j", url]
    
    if Config.HTTP_PROXY:
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])
    
    if youtube_dl_username:
        command_to_exec.extend(["--username", youtube_dl_username.strip()])
    
    if youtube_dl_password:
        command_to_exec.extend(["--password", youtube_dl_password.strip()])

    # Run yt-dlp asynchronously
    process = await asyncio.create_subprocess_exec(
        *command_to_exec, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response:
        error_message = e_response.replace(Translation.ERROR_YTDLP, "")
        if "This video is only available for registered users." in error_message:
            error_message = Translation.SET_CUSTOM_USERNAME_PASSWORD
        else:
            error_message = "Invalid URL 🚸"

        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            disable_web_page_preview=True,
            parse_mode="html",
            reply_to_message_id=update.id,
        )
        await imog.delete()
        return

    # Parse response JSON safely
    try:
        response_json = json.loads(t_response)
    except json.JSONDecodeError:
        await imog.edit_text("Failed to process video metadata. Please try another link.")
        return

    inline_keyboard = []
    duration = response_json.get("duration")

    if "formats" in response_json:
        for format in response_json["formats"]:
            format_id = format.get("format_id")
            format_note = format.get("format_note", format.get("format"))
            format_ext = format.get("ext")
            approx_file_size = humanbytes(format.get("filesize", 0))

            cb_string_video = f"video|{format_id}|{format_ext}"
            cb_string_file = f"file|{format_id}|{format_ext}"

            if format_note and "audio only" not in format_note:
                ikeyboard = [
                    InlineKeyboardButton(f"🎥 {format_note} ({approx_file_size})", callback_data=cb_string_video),
                    InlineKeyboardButton(f"📂 {format_ext} ({approx_file_size})", callback_data=cb_string_file),
                ]
            else:
                ikeyboard = [
                    InlineKeyboardButton(f"🎥 Video ({approx_file_size})", callback_data=cb_string_video),
                    InlineKeyboardButton(f"📂 File ({approx_file_size})", callback_data=cb_string_file),
                ]

            inline_keyboard.append(ikeyboard)

        if duration:
            inline_keyboard.append([
                InlineKeyboardButton("🎵 MP3 (64 kbps)", callback_data="audio|64k|mp3"),
                InlineKeyboardButton("🎵 MP3 (128 kbps)", callback_data="audio|128k|mp3"),
            ])
            inline_keyboard.append([
                InlineKeyboardButton("🎵 MP3 (320 kbps)", callback_data="audio|320k|mp3")
            ])

    else:
        format_id = response_json["format_id"]
        format_ext = response_json["ext"]
        cb_string_video = f"video|{format_id}|{format_ext}"
        cb_string_file = f"file|{format_id}|{format_ext}"

        inline_keyboard.append([
            InlineKeyboardButton("🎥 Video", callback_data=cb_string_video),
            InlineKeyboardButton("📂 File", callback_data=cb_string_file),
        ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    await imog.delete()
    await bot.send_message(
        chat_id=update.chat.id,
        text=Translation.FORMAT_SELECTION,
        reply_markup=reply_markup,
        parse_mode="html",
        reply_to_message_id=update.id,
                                              )
    
