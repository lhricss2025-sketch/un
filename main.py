#!/usr/bin/env python3
"""
WhatsApp Unban Bot - FINAL WORKING VERSION
Direct Telegram connection with Webhook mode for Railway
"""

import os
import re
import time
import json
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify

# ============================================================
# CONFIGURATION - YAHAN APNI VALUES DAALEN
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = os.environ.get("ADMIN_ID", "YOUR_CHAT_ID_HERE")

# Railway app URL (Deploy ke baad yeh set karna)
# Example: "https://your-app-name.up.railway.app"
RAILWAY_URL = os.environ.get("RAILWAY_URL", "https://your-app.railway.app")

# Gmail Accounts
GMAIL_ACCOUNTS = [
    {"email": "lhricss2025@gmail.com", "password": "uhmbtrpomqccruvs"},
    {"email": "mohsinfreefire25@gmail.com", "password": "gofjzaonxymtavq"},
    {"email": "senzo23456@gmail.com", "password": "sagdbfmqylfjcvtu"},
    {"email": "fatima.raza2369@gmail.com", "password": "uqethzgwsbouuuwc"},
    {"email": "sheikhmiqdad66@gmail.com", "password": "fngykmcuoqctinkf"},
    {"email": "senzo6473@gmail.com", "password": "irjpvfiqombxfkeb"},
    {"email": "noor.raza66666@gmail.com", "password": "uxhqwjuxjvvpsyrn"},
]

# Target WhatsApp Emails
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
TEMPLATE_1 = """Dear WhatsApp Support Team,

I am writing to formally request a review of my WhatsApp account, which has been banned without prior notice.

Phone Number: {phone}

To the best of my knowledge, I have not violated any of WhatsApp's Terms of Service or policies.

I kindly request you to conduct a thorough review of my account activity.

Thank you for your consideration.

Sincerely,
WhatsApp User"""

TEMPLATE_2 = """Dear WhatsApp Team,

My WhatsApp account ({phone}) has been permanently banned, and I believe this may have occurred due to an error.

I run a business and rely heavily on WhatsApp for communication.

I respectfully request you to urgently review my case.

Best regards,
WhatsApp Business User"""

TEMPLATE_3 = """Dear WhatsApp Support,

I am contacting you regarding the ban on my WhatsApp account ({phone}).

I have always tried to use WhatsApp in full compliance with its Terms of Service.

Please consider reinstating my account.

Kind regards,
WhatsApp User"""

TEMPLATE_4 = """Dear WhatsApp Support Team,

I recently discovered that my account ({phone}) has been banned without prior warning.

I kindly request a detailed review of my account.

Thank you for your consideration.

Sincerely,
WhatsApp User"""

TEMPLATE_5 = """Dear WhatsApp Team,

I am reaching out regarding the suspension of my WhatsApp account ({phone}).

I kindly request that your team review my account activity.

Best regards,
WhatsApp User"""

TEMPLATES = [TEMPLATE_1, TEMPLATE_2, TEMPLATE_3, TEMPLATE_4, TEMPLATE_5]

# Template pattern (15 emails per account)
TEMPLATE_PATTERN = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4]

# Settings
DELAY_BETWEEN_EMAILS = 5
DELAY_BETWEEN_ACCOUNTS = 5

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# Store user data temporarily
user_data = {}

# ============================================================
# TELEGRAM FUNCTIONS
# ============================================================

def send_telegram_message(chat_id, text, parse_mode=None):
    """Send message to Telegram user"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return None

def set_webhook():
    """Set webhook for Telegram bot"""
    webhook_url = f"{RAILWAY_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {"url": webhook_url}
    
    response = requests.post(url, json=payload)
    logger.info(f"Webhook set response: {response.json()}")
    return response.json()

# ============================================================
# EMAIL SENDER
# ============================================================

def send_email(account, to_email, template_index, phone_number):
    """Send single email"""
    try:
        template = TEMPLATES[template_index]
        body = template.replace("{phone}", phone_number)
        
        msg = MIMEMultipart()
        msg['From'] = account['email']
        msg['To'] = to_email
        msg['Subject'] = f"WhatsApp Account Appeal - {phone_number}"
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(account['email'], account['password'])
            server.send_message(msg)
        
        return True, "Success"
    except Exception as e:
        return False, str(e)

def run_email_campaign(phone_number, chat_id):
    """Run complete email campaign"""
    total_emails = len(GMAIL_ACCOUNTS) * 15
    sent_count = 0
    failed_count = 0
    email_counter = 0
    
    send_telegram_message(chat_id, f"📧 *Campaign Started*\n📱 Phone: {phone_number}\n📊 Total: {total_emails} emails\n⏱️ Estimated time: 10-12 minutes", "Markdown")
    
    for acc_idx, account in enumerate(GMAIL_ACCOUNTS):
        send_telegram_message(chat_id, f"📤 *Account {acc_idx+1}/{len(GMAIL_ACCOUNTS)}:* {account['email'][:20]}...", "Markdown")
        
        for target_idx in range(15):
            email_counter += 1
            to_email = TARGET_EMAILS[target_idx] if target_idx < 14 else TEST_EMAIL
            template_idx = TEMPLATE_PATTERN[target_idx]
            
            success, _ = send_email(account, to_email, template_idx, phone_number)
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Send progress update every 15 emails
            if email_counter % 15 == 0:
                percent = (email_counter / total_emails) * 100
                send_telegram_message(chat_id, f"📊 *Progress:* {percent:.0f}% ({email_counter}/{total_emails})\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}", "Markdown")
            
            if target_idx < 14:
                time.sleep(DELAY_BETWEEN_EMAILS)
        
        if acc_idx < len(GMAIL_ACCOUNTS) - 1:
            time.sleep(DELAY_BETWEEN_ACCOUNTS)
    
    # Send final report
    success_rate = (sent_count / total_emails) * 100
    report = f"✅ *CAMPAIGN COMPLETE!*\n\n"
    report += f"📱 Phone: {phone_number}\n"
    report += f"✅ Sent: {sent_count}\n"
    report += f"❌ Failed: {failed_count}\n"
    report += f"📊 Rate: {success_rate:.1f}%\n\n"
    report += f"📧 Check {TEST_EMAIL} for test emails."
    
    send_telegram_message(chat_id, report, "Markdown")

# ============================================================
# WEBHOOK HANDLER
# ============================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram messages"""
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({"status": "ok"}), 200
        
        logger.info(f"Received update: {update}")
        
        # Extract message data
        if 'message' in update:
            msg = update['message']
            chat_id = str(msg['chat']['id'])
            user_id = str(msg['from']['id'])
            
            # Check if user is admin
            if user_id != ADMIN_ID:
                send_telegram_message(chat_id, "❌ Unauthorized. You are not the admin.")
                return jsonify({"status": "ok"}), 200
            
            # Handle text messages
            if 'text' in msg:
                text = msg['text'].strip()
                
                # Commands
                if text == '/start':
                    send_telegram_message(chat_id, 
                        "🤖 *WhatsApp Unban Bot Activated!*\n\n"
                        "*Commands:*\n"
                        "/unban - Start unban request\n"
                        "/status - Check bot status\n"
                        "/help - Show help\n\n"
                        "⚠️ *Educational purposes only*",
                        "Markdown")
                
                elif text == '/status':
                    send_telegram_message(chat_id,
                        f"✅ *Bot Status:* Online\n"
                        f"📧 Gmail Accounts: {len(GMAIL_ACCOUNTS)}\n"
                        f"📨 Target Emails: {len(TARGET_EMAILS)}\n"
                        f"⏱️ Delay: {DELAY_BETWEEN_EMAILS} sec",
                        "Markdown")
                
                elif text == '/help':
                    send_telegram_message(chat_id,
                        "📖 *How to use:*\n\n"
                        "1. Send /unban\n"
                        "2. Enter your WhatsApp number\n"
                        "3. Type YES to confirm\n"
                        "4. Bot sends 105 emails\n\n"
                        "Send /cancel to stop.",
                        "Markdown")
                
                elif text == '/unban':
                    user_data[chat_id] = {"state": "waiting_phone"}
                    send_telegram_message(chat_id,
                        "📱 *Enter your WhatsApp number:*\n"
                        "Example: `+92302154325`\n\n"
                        "Send /cancel to cancel.",
                        "Markdown")
                
                elif text == '/cancel':
                    if chat_id in user_data:
                        del user_data[chat_id]
                    send_telegram_message(chat_id, "❌ Cancelled.")
                
                else:
                    # Handle state-based responses
                    if chat_id in user_data:
                        state = user_data[chat_id].get("state")
                        
                        if state == "waiting_phone":
                            # Validate phone number
                            if re.match(r'^\+\d{10,15}$', text):
                                user_data[chat_id]["phone"] = text
                                user_data[chat_id]["state"] = "waiting_confirm"
                                send_telegram_message(chat_id,
                                    f"✅ Phone saved: `{text}`\n\n"
                                    f"📊 Total emails: {len(GMAIL_ACCOUNTS) * 15}\n"
                                    f"⏱️ Estimated time: 10-12 minutes\n\n"
                                    f"Type *YES* to start or /cancel to abort.",
                                    "Markdown")
                            else:
                                send_telegram_message(chat_id,
                                    "❌ *Invalid format!*\n"
                                    "Use: + followed by country code and number\n"
                                    "Example: `+92302154325`",
                                    "Markdown")
                        
                        elif state == "waiting_confirm":
                            if text.upper() == "YES":
                                phone = user_data[chat_id].get("phone")
                                del user_data[chat_id]
                                
                                # Run campaign in background
                                import threading
                                threading.Thread(target=run_email_campaign, args=(phone, chat_id)).start()
                            else:
                                del user_data[chat_id]
                                send_telegram_message(chat_id, "❌ Cancelled.")
                    else:
                        send_telegram_message(chat_id, "Send /unban to start.")
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/')
def home():
    return "WhatsApp Unban Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    # Set webhook on startup
    time.sleep(2)
    set_webhook()
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info(f"Webhook URL: {RAILWAY_URL}/webhook")
    
    app.run(host="0.0.0.0", port=port)
