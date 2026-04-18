#!/usr/bin/env python3
"""
WhatsApp Unban Bot - Polling Mode with Keep-Alive
Railway par deploy karne ke liye optimized
"""

import os
import re
import time
import logging
import threading
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Tuple
from flask import Flask

# Telegram Bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIGURATION - YAHAN APNI VALUES DAALEN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Gmail Accounts
GMAIL_ACCOUNTS = [
    {"email": "lhricss2025@gmail.com", "app_password": "uhmbtrpomqccruvs"},
    {"email": "mohsinfreefire25@gmail.com", "app_password": "gofjzaonxymtavq"},
    {"email": "senzo23456@gmail.com", "app_password": "sagdbfmqylfjcvtu"},
    {"email": "fatima.raza2369@gmail.com", "app_password": "uqethzgwsbouuuwc"},
    {"email": "sheikhmiqdad66@gmail.com", "app_password": "fngykmcuoqctinkf"},
    {"email": "senzo6473@gmail.com", "app_password": "irjpvfiqombxfkeb"},
    {"email": "noor.raza66666@gmail.com", "app_password": "uxhqwjuxjvvpsyrn"},
]

# Target Emails
TARGET_EMAILS = [
    "support@support.whatsapp.com", "android@support.whatsapp.com",
    "smb_web@support.whatsapp.com", "smb@support.whatsapp.com",
    "security@whatsapp.com", "privacy@whatsapp.com",
    "accessibility@support.whatsapp.com", "iphone@support.whatsapp.com",
    "android@whatsapp.com", "support@whatsapp.com", "press@whatsapp.com",
    "android_web@support.whatsapp.com", "iphone_web@support.whatsapp.com",
    "trademark@whatsapp.com",
]

TEST_EMAIL = "senzo23456@gmail.com"

# Email Templates (Shortened for brevity - aap poori templates daal dena)
TEMPLATES = [
    {"id": 1, "subject": "Request for Review", "body": "Phone: {phone_number}\n\nDear WhatsApp Team, please review my banned account."},
    {"id": 2, "subject": "Urgent Appeal", "body": "Phone: {phone_number}\n\nUrgent: My business account is banned."},
    {"id": 3, "subject": "Account Ban Review", "body": "Phone: {phone_number}\n\nPlease review my account ban."},
    {"id": 4, "subject": "Respectful Request", "body": "Phone: {phone_number}\n\nRequesting account review."},
    {"id": 5, "subject": "Immediate Review", "body": "Phone: {phone_number}\n\nRequest immediate review."},
]

TEMPLATE_PATTERN = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]

EMAIL_CONFIG = {
    "delay_between_emails": 5,
    "delay_between_accounts": 5,
    "max_emails_per_account": 15,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
}

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# FLASK APP FOR RAILWAY KEEP-ALIVE
# ============================================================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "WhatsApp Unban Bot is running! (Polling Mode - Live)"

@flask_app.route('/health')
def health():
    return "OK", 200

# ============================================================
# EMAIL SENDER
# ============================================================

class WhatsAppEmailSender:
    def __init__(self):
        self.phone_number = None
        self.sent_count = 0
        self.failed_count = 0
    
    def send_email(self, account: Dict, to_email: str, template_id: int) -> bool:
        try:
            template = TEMPLATES[template_id - 1]
            body = template["body"].replace("{phone_number}", self.phone_number)
            
            msg = MIMEMultipart()
            msg['From'] = account['email']
            msg['To'] = to_email
            msg['Subject'] = template["subject"]
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.starttls()
                server.login(account['email'], account['app_password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Failed: {e}")
            return False
    
    def run_campaign(self, progress_callback):
        self.sent_count = 0
        self.failed_count = 0
        
        total = len(GMAIL_ACCOUNTS) * EMAIL_CONFIG["max_emails_per_account"]
        count = 0
        
        for acc_idx, account in enumerate(GMAIL_ACCOUNTS):
            for target_idx in range(EMAIL_CONFIG["max_emails_per_account"]):
                count += 1
                to_email = TARGET_EMAILS[target_idx] if target_idx < len(TARGET_EMAILS) else TEST_EMAIL
                template_id = TEMPLATE_PATTERN[target_idx]
                
                if self.send_email(account, to_email, template_id):
                    self.sent_count += 1
                else:
                    self.failed_count += 1
                
                progress_callback(count, total)
                
                if target_idx < EMAIL_CONFIG["max_emails_per_account"] - 1:
                    time.sleep(EMAIL_CONFIG["delay_between_emails"])
            
            if acc_idx < len(GMAIL_ACCOUNTS) - 1:
                time.sleep(EMAIL_CONFIG["delay_between_accounts"])
        
        return self.sent_count, self.failed_count

# ============================================================
# TELEGRAM HANDLERS
# ============================================================

user_sessions = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    logger.info(f"✅ Start command received from: {user_id}")
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "🤖 *WhatsApp Unban Bot Activated!*\n\n"
        "✅ Bot is ONLINE and WORKING!\n\n"
        "📋 *Commands:*\n"
        "/start - Show this menu\n"
        "/unban - Start unban request\n"
        "/status - Check bot status\n"
        "/help - Get help\n\n"
        "⚠️ For educational purposes only",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "✅ *Bot Status:* ONLINE ✅\n\n"
        f"📧 Gmail Accounts: {len(GMAIL_ACCOUNTS)}\n"
        f"📨 Target Emails: {len(TARGET_EMAILS)}\n"
        f"📝 Templates: {len(TEMPLATES)}\n"
        f"⏱️ Delay: {EMAIL_CONFIG['delay_between_emails']} sec\n\n"
        "Send /unban to start.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Send /unban\n"
        "2. Enter your WhatsApp number (e.g., +92302154325)\n"
        "3. Type YES to confirm\n"
        "4. Bot will send 105 emails\n\n"
        "Send /cancel to stop.",
        parse_mode="Markdown"
    )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    user_sessions[user_id] = {"state": "waiting_for_phone"}
    await update.message.reply_text(
        "📱 *Enter your WhatsApp number:*\nExample: `+92302154325`\n\nSend /cancel to cancel.",
        parse_mode="Markdown"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("❌ Cancelled.")
    else:
        await update.message.reply_text("No active operation.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    if user_id not in user_sessions:
        await update.message.reply_text("Send /unban to start.")
        return
    
    state = user_sessions[user_id]["state"]
    
    if state == "waiting_for_phone":
        phone = update.message.text.strip()
        
        if not re.match(r'^\+\d{10,15}$', phone):
            await update.message.reply_text("❌ Invalid! Use: +92302154325")
            return
        
        user_sessions[user_id]["phone"] = phone
        user_sessions[user_id]["state"] = "confirm"
        
        await update.message.reply_text(
            f"✅ Phone: `{phone}`\n\n📊 Total emails: {len(GMAIL_ACCOUNTS) * 15}\n⏱️ Time: ~10-15 mins\n\nType *YES* to start.",
            parse_mode="Markdown"
        )
    
    elif state == "confirm":
        if update.message.text.upper() == "YES":
            await update.message.reply_text("🚀 *Starting...* I'll update you when complete.", parse_mode="Markdown")
            
            def send_update(current, total):
                pass  # Optional progress
            
            sender = WhatsAppEmailSender()
            sender.phone_number = user_sessions[user_id]["phone"]
            
            sent, failed = sender.run_campaign(send_update)
            
            await update.message.reply_text(
                f"✅ *Campaign Complete!*\n\n"
                f"✅ Sent: {sent}\n"
                f"❌ Failed: {failed}\n"
                f"📊 Rate: {(sent/(sent+failed)*100):.1f}%\n\n"
                f"📧 Check {TEST_EMAIL} for test emails.",
                parse_mode="Markdown"
            )
            
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ Cancelled.")
            del user_sessions[user_id]

# ============================================================
# MAIN - POLLING MODE WITH KEEP-ALIVE
# ============================================================

def run_bot():
    """Run bot in polling mode"""
    print("🤖 Starting Telegram bot in POLLING mode...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Handlers registered!")
    print("🚀 Bot is polling...")
    
    # Start polling
    application.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    # Start bot in thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    print("✅ Bot thread started!")
    
    # Run Flask for keep-alive
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Flask server on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
