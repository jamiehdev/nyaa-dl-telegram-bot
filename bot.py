import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
import aiohttp
from qbittorrentapi import Client
from qbittorrentapi.exceptions import APIConnectionError, LoginFailed
from dotenv import load_dotenv
import traceback

# load environment variables
load_dotenv()

# set up logging to a file and console
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create handlers
file_handler = logging.FileHandler('bot_debug.log')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# configuration from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
QB_HOST = os.getenv("QB_HOST")  # hostname without protocol
QB_PORT = int(os.getenv("QB_PORT", "443"))  # port number as integer
QB_USERNAME = os.getenv("QB_USERNAME")
QB_PASSWORD = os.getenv("QB_PASSWORD")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "/home/ubuntu/downloads")
ALLOWED_USERS = [123456789]  # update with your allowed user IDs

# initialize qbittorrent client
qb_client = None

def get_qb_client():
    global qb_client
    if qb_client is None:
        qb_client = Client(
            host=QB_HOST,
            port=QB_PORT,
            username=QB_USERNAME,
            password=QB_PASSWORD,
            VERIFY_WEBUI_CERTIFICATE=True,  # set to true if using valid ssl certificates
        )
        try:
            qb_client.auth_log_in()
            logger.info("successfully connected and authenticated with qbittorrent.")
        except (APIConnectionError, LoginFailed) as e:
            logger.error(f"failed to connect or authenticate with qbittorrent: {e}")
            logger.error(f"traceback: {traceback.format_exc()}")
            raise
    return qb_client

# authentication decorator
def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            logger.warning(f"unauthorized access denied for {user_id}.")
            await update.message.reply_text("sorry, you are not authorized to use this bot.")
            return
        return await func(update, context)
    return wrapper

# function to validate torrent URLs
def is_valid_torrent_url(url):
    return url.endswith(".torrent") or url.startswith("magnet:?xt=urn:btih:")

# function to add torrent synchronously
def add_torrent(torrent_url):
    qb = get_qb_client()
    qb.torrents_add(urls=[torrent_url], save_path=DOWNLOAD_PATH)
    logger.debug(f"torrent added with URL: {torrent_url}")

# asynchronous function to handle downloading
async def download_from_url(update: Update, context: ContextTypes.DEFAULT_TYPE, torrent_url: str) -> None:
    if not is_valid_torrent_url(torrent_url):
        await update.effective_message.reply_text("invalid torrent URL. please provide a valid .torrent file link or a magnet link.")
        return

    loop = asyncio.get_event_loop()
    try:
        # run the blocking operation in a separate thread
        await loop.run_in_executor(None, add_torrent, torrent_url)
        await update.effective_message.reply_text("torrent added to qbittorrent successfully!")
    except APIConnectionError:
        await update.effective_message.reply_text("failed to connect to qbittorrent. please check the bot's configuration.")
    except LoginFailed:
        await update.effective_message.reply_text("authentication with qbittorrent failed. please verify the credentials.")
    except Exception as e:
        logger.error(f"error adding torrent: {e}")
        logger.error(f"traceback: {traceback.format_exc()}")
        await update.effective_message.reply_text("an unexpected error occurred while adding the torrent. please try again later.")

# function to search nyaa
async def search_nyaa(query):
    api_url = "https://nyaaapi.onrender.com/nyaa"
    params = {
        "q": query,
        "page": 1,
        "sort": "seeders",
        "order": "desc"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, params=params) as response:
                logger.debug(f"API request URL: {response.url}")
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"API response data: {data}")

                    # parse based on the actual response structure
                    if isinstance(data, dict):
                        torrents = data.get("data") or data.get("results") or []
                    elif isinstance(data, list):
                        torrents = data
                    else:
                        logger.error("unexpected data format from API.")
                        return []

                    if not isinstance(torrents, list):
                        logger.error("torrents data is not a list.")
                        return []

                    results = []
                    for torrent in torrents[:5]:
                        name = torrent.get("title", "no name")
                        # fetch the magnet link
                        magnet_link = torrent.get("magnet")
                        # fallback to torrent file link if magnet link is not available
                        torrent_link = magnet_link or torrent.get("torrent", "#")
                        logger.debug(f"torrent found: {name}, link: {torrent_link}")
                        results.append((name, torrent_link))
                    logger.info(f"found {len(results)} results for query: {query}")
                    return results
                else:
                    logger.error(f"API request failed with status code: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"error during nyaa API search: {str(e)}")
            return []

# /search command handler with inline buttons
@restricted
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("please provide a search query. usage: /search <query>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"searching for: {query}")

    try:
        results = await search_nyaa(query)
        if results:
            response = "search results:\n\n"
            keyboard = []
            # store search results in user_data
            context.user_data['search_results'] = {}
            for i, (name, link) in enumerate(results, 1):
                # assign a unique identifier for each result
                result_id = str(i)
                # store the link in user_data
                context.user_data['search_results'][result_id] = link
                button = InlineKeyboardButton(f"download {i}", callback_data=f"download|{result_id}")
                keyboard.append([button])
                response += f"{i}. {name}\n\n"
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            response = "no results found."
            await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"error during search: {e}")
        logger.error(f"traceback: {traceback.format_exc()}")
        response = f"an error occurred during the search: {str(e)}. please try again later."
        await update.message.reply_text(response)

# callback query handler for inline buttons
@restricted
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # acknowledge the callback

    data = query.data
    if data.startswith("download|"):
        try:
            _, result_id = data.split("|", 1)
            # retrieve the link from user_data
            torrent_url = context.user_data.get('search_results', {}).get(result_id)
            if not torrent_url:
                await query.edit_message_text("failed to retrieve the torrent URL.")
                return
            logger.debug(f"retrieved torrent URL: {torrent_url}")
            await download_from_url(update, context, torrent_url)
            await query.edit_message_text("torrent added to qbittorrent successfully!")
        except Exception as e:
            logger.error(f"error processing download: {e}")
            logger.error(f"traceback: {traceback.format_exc()}")
            await query.edit_message_text("failed to add torrent. please try again later.")
    else:
        await query.edit_message_text("unknown action.")

# /download command handler for manual downloads
@restricted
async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("please provide a torrent URL. usage: /download <url>")
        return

    torrent_url = context.args[0]
    await download_from_url(update, context, torrent_url)

# /active command handler to list active downloads
@restricted
async def active_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        qb = get_qb_client()
        torrents = qb.torrents_info()
        active = [t for t in torrents if t.state in ["downloading", "uploading"]]
        if not active:
            await update.effective_message.reply_text("no active downloads.")
            return
        response = "active downloads:\n\n"
        for t in active:
            response += f"{t.name} - {t.progress * 100:.2f}%\n"
        await update.effective_message.reply_text(response)
    except Exception as e:
        logger.error(f"error retrieving active downloads: {e}")
        logger.error(f"traceback: {traceback.format_exc()}")
        await update.effective_message.reply_text("failed to retrieve active downloads.")

# /start command handler
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "welcome to the nyaa search and download bot!\n\n"
        "commands:\n"
        "/search <query> - search for torrents on nyaa\n"
        "/download <url> - add a torrent to qbittorrent\n"
        "/active - list active downloads\n"
        "you can also use the numbered download buttons after a search."
    )

# main function to set up the bot
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    # register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("active", active_downloads))
    application.add_handler(CallbackQueryHandler(button_callback))

    # run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
