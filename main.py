#!/usr/bin/env python3
"""
WhatsApp Unban Email Bot - Telegram Controlled (Polling Mode)
Railway.com Deployment Ready
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
from flask import Flask, request
import asyncio

# Telegram Bot - Polling Mode
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ============================================================
# CONFIGURATION - EDIT THESE
# ============================================================

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Gmail Accounts (7 accounts)
GMAIL_ACCOUNTS = [
    {"email": "lhricss2025@gmail.com", "app_password": "uhmbtrpomqccruvs"},
    {"email": "mohsinfreefire25@gmail.com", "app_password": "gofjzaonxymtavq"},
    {"email": "senzo23456@gmail.com", "app_password": "sagdbfmqylfjcvtu"},
    {"email": "fatima.raza2369@gmail.com", "app_password": "uqethzgwsbouuuwc"},
    {"email": "sheikhmiqdad66@gmail.com", "app_password": "fngykmcuoqctinkf"},
    {"email": "senzo6473@gmail.com", "app_password": "irjpvfiqombxfkeb"},
    {"email": "noor.raza66666@gmail.com", "app_password": "uxhqwjuxjvvpsyrn"},
]

# Target WhatsApp Support Emails (14 addresses)
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

# Test email
TEST_EMAIL = "senzo23456@gmail.com"

# Email Templates (5 templates)
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

# Template rotation pattern
TEMPLATE_PATTERN = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]

# Email configuration
EMAIL_CONFIG = {
    "delay_between_emails": 5,
    "delay_between_accounts": 5,
    "max_emails_per_account": 15,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
}

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# FLASK APP FOR RAILWAY (Health Check)
# ============================================================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "WhatsApp Unban Bot is running! (Polling Mode)"

@flask_app.route('/health')
def health():
    return "OK", 200

# ============================================================
# EMAIL SENDER CLASS
# ============================================================

class WhatsAppEmailSender:
    def __init__(self):
        self.phone_number = None
        self.sent_count = 0
        self.failed_count = 0
        self.results = []
    
    def send_email(self, account: Dict, to_email: str, template_id: int) -> Tuple[bool, str]:
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
            
            logger.info(f"✓ Sent from {account['email']} to {to_email}")
            return True, "Success"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ Failed: {error_msg}")
            return False, error_msg
    
    def run_campaign(self, progress_callback=None):
        self.sent_count = 0
        self.failed_count = 0
        self.results = []
        
        total_emails = len(GMAIL_ACCOUNTS) * EMAIL_CONFIG["max_emails_per_account"]
        email_counter = 0
        
        for acc_idx, account in enumerate(GMAIL_ACCOUNTS):
            account_result = {
                "account": account['email'],
                "sent": 0,
                "failed": 0,
                "details": []
            }
            
            for target_idx in range(EMAIL_CONFIG["max_emails_per_account"]):
                email_counter += 1
                to_email = TARGET_EMAILS[target_idx] if target_idx < len(TARGET_EMAILS) else TEST_EMAIL
                template_id = TEMPLATE_PATTERN[target_idx]
                is_test = (target_idx == 14)
                
                success, message = self.send_email(account, to_email, template_id)
                
                if success:
                    self.sent_count += 1
                    account_result["sent"] += 1
                else:
                    self.failed_count += 1
                    account_result["failed"] += 1
                
                account_result["details"].append({
                    "to": to_email,
                    "template": template_id,
                    "success": success,
                    "is_test": is_test
                })
                
                if progress_callback:
                    progress_callback(email_counter, total_emails, to_email, success, is_test)
                
                if target_idx < EMAIL_CONFIG["max_emails_per_account"] - 1:
                    time.sleep(EMAIL_CONFIG["delay_between_emails"])
            
            self.results.append(account_result)
            
            if acc_idx < len(GMAIL_ACCOUNTS) - 1:
                time.sleep(EMAIL_CONFIG["delay_between_accounts"])
        
        return {
            "total_sent": self.sent_count,
            "total_failed": self.failed_count,
            "success_rate": (self.sent_count / (self.sent_count + self.failed_count)) * 100 if (self.sent_count + self.failed_count) > 0 else 0,
            "results": self.results
        }

# ============================================================
# TELEGRAM BOT HANDLERS (POLLING MODE)
# ============================================================

# User sessions
user_sessions = {}

# Conversation states
PHONE_NUMBER, CONFIRMATION = range(2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    
    logger.info(f"Start command received from user: {user_id}")
    
    # Check if user is admin
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "🤖 *WhatsApp Unban Bot Activated!*\n\n"
        "I can send unban requests to WhatsApp support using 7 different Gmail accounts.\n\n"
        "*Commands:*\n"
        "/start - Show this menu\n"
        "/unban - Start the unban request process\n"
        "/status - Check bot status\n"
        "/help - Show help\n\n"
        "⚠️ *For educational purposes only*",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Send /unban to start\n"
        "2. Enter your WhatsApp number with country code\n"
        "3. Bot will send 105 emails (15 from each of 7 accounts)\n"
        "4. You'll receive progress updates\n"
        "5. Final report will be sent when complete\n\n"
        "*Example number:* +92302154325",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "✅ *Bot Status:* Running (Polling Mode)\n\n"
        f"📧 *Gmail Accounts:* {len(GMAIL_ACCOUNTS)}\n"
        f"📨 *Target Emails:* {len(TARGET_EMAILS)} WhatsApp addresses + 1 test\n"
        f"📝 *Templates:* {len(TEMPLATES)}\n"
        f"⏱️ *Delay:* {EMAIL_CONFIG['delay_between_emails']} seconds\n\n"
        "Send /unban to start sending emails.",
        parse_mode="Markdown"
    )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    user_sessions[user_id] = {"state": "waiting_for_phone"}
    
    await update.message.reply_text(
        "📱 *Please enter your WhatsApp phone number*\n\n"
        "Format: + followed by country code and number\n"
        "Example: `+92302154325`\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("❌ Operation cancelled.")
    else:
        await update.message.reply_text("No active operation to cancel.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    if user_id not in user_sessions:
        await update.message.reply_text("Send /unban to start the process.")
        return
    
    state = user_sessions[user_id]["state"]
    
    if state == "waiting_for_phone":
        phone_number = update.message.text.strip()
        
        # Validate phone number
        if not re.match(r'^\+\d{10,15}$', phone_number):
            await update.message.reply_text(
                "❌ *Invalid phone number format*\n\n"
                "Please use: + followed by country code and number\n"
                "Example: `+92302154325`\n\n"
                "Send /cancel to cancel.",
                parse_mode="Markdown"
            )
            return
        
        user_sessions[user_id]["phone_number"] = phone_number
        user_sessions[user_id]["state"] = "confirm"
        
        await update.message.reply_text(
            f"✅ *Phone number saved:* `{phone_number}`\n\n"
            f"📊 *Campaign Details:*\n"
            f"• {len(GMAIL_ACCOUNTS)} Gmail accounts\n"
            f"• {len(TARGET_EMAILS)} WhatsApp support emails + 1 test\n"
            f"• Total emails: {len(GMAIL_ACCOUNTS) * 15}\n\n"
            f"⚠️ This will take approximately 10-15 minutes.\n\n"
            f"Type *YES* to confirm and start sending.",
            parse_mode="Markdown"
        )
    
    elif state == "confirm":
        if update.message.text.upper() == "YES":
            await update.message.reply_text(
                "🚀 *Starting email campaign...*\n\n"
                "I'll send you progress updates. This may take 10-15 minutes.",
                parse_mode="Markdown"
            )
            
            # Start email sending in background
            threading.Thread(target=run_email_campaign, args=(update, context, user_sessions[user_id]["phone_number"])).start()
            
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ Cancelled. Send /unban to start over.")
            del user_sessions[user_id]

def run_email_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str):
    """Run email campaign in background"""
    import asyncio
    
    sender = WhatsAppEmailSender()
    sender.phone_number = phone_number
    
    async def send_update(text):
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="Markdown")
    
    # Send initial message
    try:
        asyncio.run(send_update(f"📧 *Email Campaign Started*\n\n📱 Phone: `{phone_number}`\n⏱️ Estimated time: 10-15 minutes\n\nSending emails..."))
    except:
        pass
    
    def progress_callback(current, total, to_email, success, is_test):
        if current % 15 == 0 or current == total:
            percent = (current / total) * 100
            try:
                asyncio.run(send_update(f"📊 *Progress:* {percent:.1f}% ({current}/{total})\n✅ Sent: {sender.sent_count}\n❌ Failed: {sender.failed_count}"))
            except:
                pass
    
    # Run campaign
    result = sender.run_campaign(progress_callback)
    
    # Prepare final report
    report = f"✅ *Email Campaign Complete!*\n\n"
    report += f"📱 Phone: `{phone_number}`\n"
    report += f"✅ Successfully sent: {result['total_sent']}\n"
    report += f"❌ Failed: {result['total_failed']}\n"
    report += f"📊 Success rate: {result['success_rate']:.1f}%\n\n"
    report += f"📧 *Test emails:* You should receive {len(GMAIL_ACCOUNTS)} test emails at `{TEST_EMAIL}`\n\n"
    report += f"⚠️ Check your spam folder if you don't see them."
    
    report += "\n\n📋 *Per Account Summary:*\n"
    for acc_result in result['results']:
        status = "✅" if acc_result['failed'] == 0 else "⚠️"
        report += f"{status} {acc_result['account'][:20]}...: {acc_result['sent']}/15 sent\n"
    
    try:
        asyncio.run(send_update(report))
    except:
        pass

# ============================================================
# MAIN FUNCTION - POLLING MODE
# ============================================================

def run_bot():
    """Run the bot in polling mode"""
    print("🤖 Starting Telegram bot in POLLING mode...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot handlers registered!")
    print(f"📧 Gmail accounts: {len(GMAIL_ACCOUNTS)}")
    print(f"📨 Target emails: {len(TARGET_EMAILS)}")
    print("🚀 Starting polling...")
    
    # Start polling (this blocks)
    application.run_polling(allowed_updates=["message", "callback_query"])

# ============================================================
# RUN THE APPLICATION
# ============================================================

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    print("✅ Bot thread started!")
    
    # Run Flask app for Railway health checks
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting Flask server on port {port}...")
    flask_app.run(host="0.0.0.0", port=port)
