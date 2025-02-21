#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from config import Config
from pyrogram import Client

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Create download directory if it doesn't exist
    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)

    # Initialize the bot client properly
    Warrior = Client(
        "bot",  # Changed from "@WebXBots" to a proper session name
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        plugins=dict(root="plugins")  # Ensure plugins are correctly loaded
    )

    # Run the bot
    Warrior.run()
    
