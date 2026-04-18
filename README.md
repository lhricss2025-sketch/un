# WhatsApp Unban Email Bot

Telegram bot that sends unban requests to WhatsApp support using 7 Gmail accounts.

## Setup Instructions

### 1. Get Telegram Bot Token
- Message @BotFather on Telegram
- Send `/newbot` and follow instructions
- Copy the bot token

### 2. Get Your Chat ID
- Message @userinfobot on Telegram
- Copy your chat ID

### 3. Update Configuration
Open `main.py` and edit:
- `TELEGRAM_BOT_TOKEN = "your_token_here"`
- `ADMIN_CHAT_ID = "your_chat_id_here"`

### 4. Deploy on Railway
- Push code to GitHub
- Connect repository to Railway
- Add environment variables (optional)

### 5. Run Locally
```bash
pip install -r requirements.txt
python main.py
