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

# Configure SQLite database
database_path = os.path.join(os.getcwd(), "db", "chat_logs.sqlite")
os.makedirs(os.path.dirname(database_path), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
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
        
        # For now, just log the update and return OK
        # TODO: Process the update with dispatcher
        logging.info("Webhook received successfully")
        
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
        "endpoints": ["/webhook", "/health"]
    })

# Create documents directory
os.makedirs("db/documents", exist_ok=True)
