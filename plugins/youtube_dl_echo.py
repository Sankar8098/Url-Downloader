@Clinton.on_message(filters.private & ~filters.via_bot & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    await AddUser(bot, update)
    imog = await update.reply_text("Processing...⚡", reply_to_message_id=update.id)  # Fixed attribute issue

    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    url = update.text

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
                    url = url[entity.offset: entity.offset + entity.length]

    url = url.strip() if url else None
    file_name = file_name.strip() if file_name else None
    youtube_dl_username = youtube_dl_username.strip() if youtube_dl_username else None
    youtube_dl_password = youtube_dl_password.strip() if youtube_dl_password else None

    logger.info(url)
    logger.info(file_name)

    command_to_exec = [
        "yt-dlp",
        "--no-warnings",
        "--youtube-skip-dash-manifest",
        "-j",
        url
    ]
    if Config.HTTP_PROXY:
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])
    if youtube_dl_username:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password:
        command_to_exec.extend(["--password", youtube_dl_password])

    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(Translation.ERROR_YTDLP, "")
        if "This video is only available for registered users." in error_message:
            error_message = Translation.SET_CUSTOM_USERNAME_PASSWORD
        else:
            error_message = "Invalid URL 🚸"

        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            disable_web_page_preview=True,
            parse_mode="HTML",  # Fixed parse mode issue
            reply_to_message_id=update.id
        )
        await imog.delete()
        return

    if t_response:
        response_json = json.loads(t_response.split("\n")[0])
        save_ytdl_json_path = os.path.join(Config.DOWNLOAD_LOCATION, f"{update.from_user.id}.json")

        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        inline_keyboard = []
        duration = response_json.get("duration")

        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note", formats.get("format", "Unknown"))
                format_ext = formats.get("ext")
                approx_file_size = humanbytes(formats.get("filesize", 0))

                cb_string_video = f"video|{format_id}|{format_ext}"
                cb_string_file = f"file|{format_id}|{format_ext}"

                if "audio only" not in format_string:
                    ikeyboard = [
                        InlineKeyboardButton(f"S {format_string} {approx_file_size}", callback_data=cb_string_video),
                        InlineKeyboardButton(f"D {format_ext} {approx_file_size}", callback_data=cb_string_file)
                    ]
                    inline_keyboard.append(ikeyboard)

            if duration:
                inline_keyboard.append([
                    InlineKeyboardButton("MP3 (64 kbps)", callback_data="audio|64k|mp3"),
                    InlineKeyboardButton("MP3 (128 kbps)", callback_data="audio|128k|mp3")
                ])
                inline_keyboard.append([
                    InlineKeyboardButton("MP3 (320 kbps)", callback_data="audio|320k|mp3")
                ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await imog.delete()
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"{Translation.FORMAT_SELECTION}\n{Translation.SET_CUSTOM_USERNAME_PASSWORD}",
            reply_markup=reply_markup,
            parse_mode="HTML",
            reply_to_message_id=update.id
        )
    else:
        await imog.delete()
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION,
            parse_mode="HTML",
            reply_to_message_id=update.id
                )
                
