# WOM Discord Sync Bot

This bot automatically synchronizes Discord roles with Wise Old Man (WOM) group ranks.  
It supports both manual sync via a slash command and automated sync every 5 minutes.

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/Sharpienero/WOM-to-Discord-Rank-Syncer.git
cd WOM-To-Discord-Rank-Syncer
```

### 2. Create and Activate a Virtual Environment

**Windows:**
```sh
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements

```sh
pip install -U pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file or set the following environment variables in your shell:

- `BOT_TOKEN` — Your Discord bot token
- `DISCORD_GUILD_ID` — Your Discord server (guild) ID
- `WOM_GROUP_ID` — Your WOM group ID
- `WOM_API_KEY` — Your WOM API key

**Example `.env` file:**
```
BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=123456789012345678
WOM_GROUP_ID=1234
WOM_API_KEY=your_wom_api_key
```

### 5. Run the Bot

```sh
python wom-sync.py
```

## Usage

- The bot will automatically sync roles every 5 minutes.
- To manually trigger a sync, use the `/sync-wom-ranks` slash command in your Discord server.

---

**Note:**  
Make sure your bot has the `Manage Roles` permission and the `applications.commands` scope when invited to your server.