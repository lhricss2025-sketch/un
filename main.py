#!/usr/bin/env python3
"""
WhatsApp Unban Email Bot - WEBHOOK MODE for Railway
Yeh mode Railway ke liye best hai
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
from flask import Flask, request, jsonify

# Telegram Bot - Webhook Mode
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Railway URL (IMPORTANT: Isko Railway deploy ke baad update karna)
RAILWAY_URL = os.environ.get("RAILWAY_URL", "https://your-app-name.railway.app")

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

# Target WhatsApp Support Emails
TARGET_EMAILS = [
    "support@support.whatsapp.com",
    "android@support.whatsapp.com",
    "smb_web@support.whatsapp.com",
    "smb@support.whatsapp.com",
    "security@whatsapp.com",
    "privacy@whatsapp.com",
    "accessibility@support.whatsapp.com",
    "iphone@support.whatsapp.com",
    "android@whatsapp.com",
    "support@whatsapp.com",
    "press@whatsapp.com",
    "android_web@support.whatsapp.com",
    "iphone_web@support.whatsapp.com",
    "trademark@whatsapp.com",
]

TEST_EMAIL = "senzo23456@gmail.com"

# Email Templates
TEMPLATES = [
    {
        "id": 1,
        "subject": "Request for Review and Reinstatement of Banned WhatsApp Account",
        "body": """Dear WhatsApp Support Team,

I am writing to formally request a review of my WhatsApp account, which has been banned without prior notice.

Phone Number: {phone_number}

To the best of my knowledge, I have not violated any of WhatsApp's Terms of Service or policies. I have always used the platform responsibly, strictly avoiding spam, bulk messaging, or any inappropriate content.

This account is very important to me, as I use WhatsApp for essential communication, including business-related interactions with clients and partners. The sudden suspension has significantly disrupted my work.

I kindly request you to conduct a thorough review of my account activity. If this action was taken due to any misunderstanding or automated system error, I would sincerely appreciate your assistance in restoring my account.

I assure you that I will continue to comply fully with all WhatsApp policies in the future.

Thank you for your time and consideration.

Sincerely,
WhatsApp User"""
    },
    {
        "id": 2,
        "subject": "Urgent Appeal – Business Account Suspended",
        "body": """Dear WhatsApp Team,

I hope you are doing well.

My WhatsApp account ({phone_number}) has been permanently banned, and I believe this may have occurred due to an error. I have always followed WhatsApp guidelines and have not engaged in any activity that violates the platform's policies.

I run a business and rely heavily on WhatsApp for communication with customers, suppliers, and partners. Due to this suspension, I am facing serious operational and financial difficulties.

I respectfully request you to urgently review my case and restore my account. Your assistance in resolving this matter would mean a great deal to me.

Thank you for your support.

Best regards,
WhatsApp Business User"""
    },
    {
        "id": 3,
        "subject": "Account Ban Review Request – Compliance Confirmation",
        "body": """Dear WhatsApp Support,

I am contacting you regarding the ban on my WhatsApp account ({phone_number}).

I would like to confirm that I have always tried to use WhatsApp in full compliance with its Terms of Service. I do not send spam, automated messages, or any content that could harm other users.

If my account was flagged unintentionally or due to unusual activity, I kindly request a manual review of my case. I am fully willing to follow any additional guidelines required to ensure compliance.

Please consider reinstating my account if possible.

Thank you for your time.

Kind regards,
WhatsApp User"""
    },
    {
        "id": 4,
        "subject": "Respectful Request for Account Re-evaluation",
        "body": """Dear WhatsApp Support Team,

I recently discovered that my account ({phone_number}) has been banned without prior warning.

I fully respect WhatsApp's policies and community standards, and I have always made sure to use the platform responsibly. I have not knowingly engaged in spam, bulk messaging, or any prohibited activities.

Given this, I believe the ban may have been applied in error. I kindly request a detailed review of my account.

This account is extremely important for my daily communication, and I would be very grateful if you could assist in restoring access.

Thank you for your consideration.

Sincerely,
WhatsApp User"""
    },
    {
        "id": 5,
        "subject": "Request for Immediate Review – Possible Incorrect Ban",
        "body": """Dear WhatsApp Team,

I am reaching out regarding the suspension of my WhatsApp account ({phone_number}).

I strongly believe that this ban may have been applied incorrectly, as I have not violated any of WhatsApp's usage policies. My usage has always been normal, without spam or misuse.

I kindly request that your team review my account activity and verify this situation. If the ban was triggered mistakenly, I request immediate restoration of my account.

I appreciate your prompt attention to this matter.

Best regards,
WhatsApp User"""
    }
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# FLASK APP
# ============================================================

flask_app = Flask(__name__)

# Global application variable for webhook
application = None

# User sessions
user_sessions = {}

# ============================================================
# EMAIL SENDER CLASS
# ============================================================

class WhatsAppEmailSender:
    def __init__(self):
        self.phone_number = None
        self.sent_count = 0
        self.failed_count = 0
        self.results = []
    
    def send_email(self, account: Dict, to_email: str, template_id: int) -> tuple:
        try:
            template = TEMPLATES[template_id - 1]
            body = template["body"].replace("{phone_number}", self.phone_number)
            
            msg = MIMEMultipart()
            msg['From'] = account['email']
            msg['To'] = to_email
            msg['Subject'] = template["subject"]
            
            body_with_timestamp = f"{body}\n\n---\nSent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body_with_timestamp, 'plain'))
            
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.starttls()
                server.login(account['email'], account['app_password'])
                server.send_message(msg)
            
            logger.info(f"✓ Sent from {account['email']}")
            return True, "Success"
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            return False, str(e)
    
    def run_campaign(self, send_update_func):
        self.sent_count = 0
        self.failed_count = 0
        
        total_emails = len(GMAIL_ACCOUNTS) * EMAIL_CONFIG["max_emails_per_account"]
        email_counter = 0
        
        for acc_idx, account in enumerate(GMAIL_ACCOUNTS):
            for target_idx in range(EMAIL_CONFIG["max_emails_per_account"]):
                email_counter += 1
                to_email = TARGET_EMAILS[target_idx] if target_idx < len(TARGET_EMAILS) else TEST_EMAIL
                template_id = TEMPLATE_PATTERN[target_idx]
                is_test = (target_idx == 14)
                
                success, _ = self.send_email(account, to_email, template_id)
                
                if success:
                    self.sent_count += 1
                else:
                    self.failed_count += 1
                
                if email_counter % 15 == 0 or email_counter == total_emails:
                    percent = (email_counter / total_emails) * 100
                    send_update_func(f"📊 *Progress:* {percent:.1f}% ({email_counter}/{total_emails})\n✅ Sent: {self.sent_count}\n❌ Failed: {self.failed_count}")
                
                if target_idx < EMAIL_CONFIG["max_emails_per_account"] - 1:
                    time.sleep(EMAIL_CONFIG["delay_between_emails"])
            
            if acc_idx < len(GMAIL_ACCOUNTS) - 1:
                time.sleep(EMAIL_CONFIG["delay_between_accounts"])
        
        return {
            "total_sent": self.sent_count,
            "total_failed": self.failed_count,
            "success_rate": (self.sent_count / (self.sent_count + self.failed_count)) * 100 if (self.sent_count + self.failed_count) > 0 else 0
        }

# ============================================================
# TELEGRAM HANDLERS
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    logger.info(f"Start command from: {user_id}")
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "🤖 *WhatsApp Unban Bot Activated!*\n\n"
        "Send /unban to start the process.\n"
        "Send /status to check bot status.\n\n"
        "⚠️ *For educational purposes only*",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "✅ *Bot Status:* Running (Webhook Mode)\n\n"
        f"📧 Gmail Accounts: {len(GMAIL_ACCOUNTS)}\n"
        f"📨 Target Emails: {len(TARGET_EMAILS)}\n"
        "Send /unban to start.",
        parse_mode="Markdown"
    )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    user_sessions[user_id] = {"state": "waiting_for_phone"}
    
    await update.message.reply_text(
        "📱 *Enter your WhatsApp number*\n\nExample: `+92302154325`\n\nSend /cancel to cancel.",
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
        phone_number = update.message.text.strip()
        
        if not re.match(r'^\+\d{10,15}$', phone_number):
            await update.message.reply_text("❌ Invalid format. Use: +92302154325")
            return
        
        user_sessions[user_id]["phone_number"] = phone_number
        user_sessions[user_id]["state"] = "confirm"
        
        await update.message.reply_text(
            f"✅ Phone: `{phone_number}`\n\n"
            f"Total emails: {len(GMAIL_ACCOUNTS) * 15}\n"
            f"Type *YES* to start.",
            parse_mode="Markdown"
        )
    
    elif state == "confirm":
        if update.message.text.upper() == "YES":
            await update.message.reply_text("🚀 Starting campaign...")
            
            def send_update(text):
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(update.message.reply_text(text, parse_mode="Markdown"))
                    loop.close()
                except:
                    pass
            
            sender = WhatsAppEmailSender()
            sender.phone_number = user_sessions[user_id]["phone_number"]
            
            result = sender.run_campaign(send_update)
            
            report = f"✅ *Complete!*\n✅ Sent: {result['total_sent']}\n❌ Failed: {result['total_failed']}\n📊 Rate: {result['success_rate']:.1f}%"
            await update.message.reply_text(report, parse_mode="Markdown")
            
            del user_sessions[user_id]
        else:
            await update.message.reply_text("Cancelled.")
            del user_sessions[user_id]

# ============================================================
# FLASK ROUTES
# ============================================================

@flask_app.route('/')
def home():
    return "WhatsApp Unban Bot is running! (Webhook Mode)"

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route(f'/webhook/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
async def webhook():
    """Handle incoming Telegram updates"""
    if request.method == 'POST':
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            await application.process_update(update)
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return jsonify({"status": "error"}), 500
    return jsonify({"status": "ok"})

# ============================================================
# MAIN
# ============================================================

def setup_webhook():
    """Setup webhook with Telegram"""
    webhook_url = f"{RAILWAY_URL}/webhook/{TELEGRAM_BOT_TOKEN}"
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        response = requests.post(url, json={"url": webhook_url})
        if response.json().get("ok"):
            logger.info(f"✅ Webhook set to: {webhook_url}")
        else:
            logger.error(f"❌ Webhook failed: {response.json()}")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")

if __name__ == "__main__":
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Initialize bot
    application.bot = Bot(token=TELEGRAM_BOT_TOKEN)
    application.initialize()
    
    # Setup webhook
    setup_webhook()
    
    # Run Flask app
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
