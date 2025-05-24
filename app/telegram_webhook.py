import os
import json
import logging
from flask import Blueprint, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.dispatcher import TelegramDispatcher
from utils.logger import get_logger

logger = get_logger(__name__)

webhook_bp = Blueprint('webhook', __name__)

# Initialize Telegram Bot
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = TelegramDispatcher(bot)

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram webhook updates"""
    try:
        data = request.get_json()
        logger.debug(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        if not data:
            logger.warning("No data received in webhook")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Create Update object from received data
        update = Update.de_json(data, bot)
        if not update:
            logger.warning("Failed to parse update from webhook data")
            return jsonify({"status": "error", "message": "Invalid update"}), 400
        
        # Process the update
        dispatcher.process_update(update)
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set the webhook URL for the Telegram bot"""
    try:
        webhook_url = request.json.get('webhook_url')
        if not webhook_url:
            return jsonify({"status": "error", "message": "webhook_url required"}), 400
        
        # Set webhook
        success = bot.set_webhook(url=webhook_url + '/webhook')
        
        if success:
            logger.info(f"Webhook set successfully to: {webhook_url}/webhook")
            return jsonify({"status": "ok", "message": "Webhook set successfully"})
        else:
            logger.error("Failed to set webhook")
            return jsonify({"status": "error", "message": "Failed to set webhook"}), 500
            
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get current webhook information"""
    try:
        webhook_info = bot.get_webhook_info()
        return jsonify({
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        })
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot_username": bot.username if hasattr(bot, 'username') else "unknown",
        "service": "telegram_bot_ai"
    })
