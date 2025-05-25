import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    db.create_all()

# Create basic webhook routes directly in app.py for now
from flask import request, jsonify
import json
import os

# Basic webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram webhook updates"""
    try:
        data = request.get_json()
        logging.debug(f"Received webhook data: {json.dumps(data, indent=2) if data else 'No data'}")
        
        if not data:
            logging.warning("No data received in webhook")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Process the update with dispatcher
        from app.telegram_webhook import process_telegram_update
        process_telegram_update(data)
        
        logging.info("Webhook processed successfully")
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "telegram_bot_ai"
    })

@app.route('/', methods=['GET'])
def index():
    """Index page"""
    return jsonify({
        "message": "Bot Telegram AI - Konstruksi & Pajak",
        "status": "running",
        "endpoints": ["/webhook", "/health", "/set-webhook"]
    })

@app.route('/set-webhook', methods=['POST', 'GET'])
def set_webhook():
    """Set Telegram webhook"""
    try:
        if request.method == 'GET':
            # Show form to set webhook
            return jsonify({
                "message": "Send POST request with webhook_url to set webhook",
                "example": {"webhook_url": "https://your-domain.replit.app"}
            })
        
        # Get webhook URL from request or use current domain
        data = request.get_json() or {}
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            # Try to auto-detect the domain
            webhook_url = request.url_root.rstrip('/')
        
        import requests
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        if not telegram_token:
            return jsonify({"error": "TELEGRAM_BOT_TOKEN not configured"}), 500
        
        # Set webhook
        response = requests.post(
            f"https://api.telegram.org/bot{telegram_token}/setWebhook",
            json={
                "url": f"{webhook_url}/webhook",
                "allowed_updates": ["message", "callback_query"]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info(f"Webhook set successfully to: {webhook_url}/webhook")
                return jsonify({
                    "status": "success", 
                    "message": "Webhook set successfully",
                    "webhook_url": f"{webhook_url}/webhook"
                })
            else:
                return jsonify({"error": f"Telegram error: {result.get('description')}"}), 400
        else:
            return jsonify({"error": "Failed to communicate with Telegram"}), 500
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({"error": f"Error setting webhook: {str(e)}"}), 500

# Create documents directory
os.makedirs("db/documents", exist_ok=True)
