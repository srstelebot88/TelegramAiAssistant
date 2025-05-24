import os
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Import models
from models import ChatSession, ChatMessage, DocumentUpload, MemoryContext

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app"""
    # Startup
    logger.info("Starting FastAPI Telegram AI Bot...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Create documents directory
    os.makedirs("db/documents", exist_ok=True)
    logger.info("Documents directory created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI Telegram AI Bot...")

# Create FastAPI app
app = FastAPI(
    title="Bot Telegram AI - Konstruksi & Pajak",
    description="Bot AI komprehensif untuk analisis konstruksi dan perpajakan Indonesia",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bot Telegram AI - Konstruksi & Pajak",
        "status": "running",
        "framework": "FastAPI",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "docs": "/docs",
            "status": "/bot-status"
        }
    }

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming Telegram webhook updates"""
    try:
        data = await request.json()
        logger.debug(f"Received webhook data: {json.dumps(data, indent=2) if data else 'No data'}")
        
        if not data:
            logger.warning("No data received in webhook")
            raise HTTPException(status_code=400, detail="No data received")
        
        # For now, log the update and return OK
        # TODO: Process the update with dispatcher
        logger.info("Webhook received successfully")
        
        return {"status": "ok", "message": "Webhook processed"}
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with SessionLocal() as db:
            db.query(ChatSession).first()
        
        return {
            "status": "healthy",
            "service": "telegram_bot_ai",
            "framework": "FastAPI",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/bot-status")
async def bot_status():
    """Get bot status and statistics"""
    try:
        with SessionLocal() as db:
            # Get basic statistics
            total_sessions = db.query(ChatSession).count()
            total_messages = db.query(ChatMessage).count()
            total_documents = db.query(DocumentUpload).count()
            
            # Check API keys
            api_keys_status = {
                "telegram_bot_token": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
                "together_api_key": bool(os.environ.get("TOGETHER_API_KEY")),
                "anthropic_api_key": bool(os.environ.get("ANTHROPIC_API_KEY"))
            }
            
            return {
                "bot_info": {
                    "name": "SRSBOT",
                    "username": "SRSTeleBot"
                },
                "statistics": {
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "total_documents": total_documents
                },
                "api_keys": api_keys_status,
                "features": [
                    "AI Chat for Construction & Tax",
                    "Document Analysis (PDF, DOCX, XLSX)",
                    "OCR for Technical Images",
                    "Volume & Cost Calculations",
                    "Construction Knowledge Base"
                ]
            }
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

@app.post("/set-webhook")
async def set_webhook(request: Request):
    """Set Telegram webhook"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        # Import here to avoid circular imports
        import requests
        
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not telegram_token:
            raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")
        
        # Set webhook with Telegram
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
                return {"status": "success", "message": "Webhook set successfully"}
            else:
                logger.error(f"Telegram API error: {result}")
                raise HTTPException(status_code=400, detail=f"Telegram error: {result.get('description')}")
        else:
            raise HTTPException(status_code=500, detail="Failed to communicate with Telegram")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting webhook: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")