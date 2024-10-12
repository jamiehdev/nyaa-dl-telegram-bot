
# nyaa dl telegram bot

a telegram bot to search and download torrents from nyaa directly to qbittorrent.

## features

- search nyaa for torrents
- add torrents to qbittorrent remotely
- list active downloads
- inline buttons for quick downloading

## requirements

- python 3.10+
- qbittorrent with web ui enabled
- telegram bot token

## installation

### windows setup

1. **create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **configure environment variables**

   copy the `.env.example` file to `.env`:

   ```bash
   copy .env.example .env
   ```

   open `.env` in a text editor and fill in your details:

   ```makefile
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   QB_HOST=localhost
   QB_PORT=8080  # use the port from qbittorrent settings
   QB_USERNAME=your_qbittorrent_username
   QB_PASSWORD=your_qbittorrent_password
   DOWNLOAD_PATH=C:\path\to\your\download\directory
   ```

3. **update ALLOWED_USERS in bot.py with your telegram user id:**

   ```python
   ALLOWED_USERS = [your_telegram_user_id]
   ```

4. **run the bot**

   ```bash
   python bot.py
   ```

### linux setup

1. **install python**

   python 3.10+ is required. you can check your python version:

   ```bash
   python3 --version
   ```

   if you need to install or update python, refer to your distribution's documentation.

2. **install qbittorrent**

   install qbittorrent using your package manager:

   ```bash
   # for debian/ubuntu
   sudo apt update
   sudo apt install qbittorrent

   # for fedora
   sudo dnf install qbittorrent

   # for arch linux
   sudo pacman -S qbittorrent
   ```

   enable the web ui:
   - open qbittorrent.
   - go to tools > options > web ui.
   - check "enable the web user interface (remote control)".
   - set a username and password.
   - note the port number (default is 8080).

3. **get your telegram bot token**

   - open telegram and start a chat with @botfather.
   - send `/newbot` and follow the instructions to create a new bot.
   - copy the bot token provided by botfather.

4. **clone the repository**

   ```bash
   git clone https://github.com/yourusername/nyaa-dl-telegram-bot.git
   cd nyaa-dl-telegram-bot
   ```

5. **create a virtual environment and install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **configure environment variables**

   copy the `.env.example` file to `.env`:

   ```bash
   cp .env.example .env
   ```

   open `.env` in a text editor and fill in your details:

   ```makefile
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   QB_HOST=localhost
   QB_PORT=8080  # use the port from qbittorrent settings
   QB_USERNAME=your_qbittorrent_username
   QB_PASSWORD=your_qbittorrent_password
   DOWNLOAD_PATH=/path/to/your/download/directory
   ```

7. **update ALLOWED_USERS in bot.py with your telegram user id:**

   ```python
   ALLOWED_USERS = [your_telegram_user_id]
   ```

8. **run the bot**

   ```bash
   python3 bot.py
   ```

## additional notes

- make sure qbittorrent's web ui is accessible from where you're running the bot.
- if qbittorrent is running on a different machine, replace `localhost` with the appropriate hostname or ip address in your `.env` file.
- ensure that the port number, username, and password in your `.env` file match the settings in qbittorrent.
- to find your telegram user id, you can use the @userinfobot on telegram.	

## commands

- `/start` - display welcome message
- `/search <query>` - search for torrents on nyaa
- `/download <url>` - add a torrent to qbittorrent
- `/active` - list active downloads

## license

mit
