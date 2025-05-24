from app import db
from datetime import datetime
from sqlalchemy import Text, DateTime, Integer, String, Boolean, LargeBinary

class ChatSession(db.Model):
    """Model for storing chat sessions and user data"""
    id = db.Column(Integer, primary_key=True)
    telegram_user_id = db.Column(String(64), unique=True, nullable=False, index=True)
    username = db.Column(String(64), nullable=True)
    first_name = db.Column(String(64), nullable=True)
    last_name = db.Column(String(64), nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    last_activity = db.Column(DateTime, default=datetime.utcnow)
    is_active = db.Column(Boolean, default=True)

class ChatMessage(db.Model):
    """Model for storing individual chat messages"""
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(Integer, db.ForeignKey('chat_session.id'), nullable=False)
    message_type = db.Column(String(20), nullable=False)  # 'user' or 'bot'
    content = db.Column(Text, nullable=False)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    telegram_message_id = db.Column(String(64), nullable=True)
    
    session = db.relationship('ChatSession', backref=db.backref('messages', lazy=True))

class DocumentUpload(db.Model):
    """Model for tracking uploaded documents"""
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(Integer, db.ForeignKey('chat_session.id'), nullable=False)
    filename = db.Column(String(255), nullable=False)
    file_path = db.Column(String(500), nullable=False)
    file_type = db.Column(String(50), nullable=False)
    file_size = db.Column(Integer, nullable=False)
    upload_timestamp = db.Column(DateTime, default=datetime.utcnow)
    processed = db.Column(Boolean, default=False)
    processing_result = db.Column(Text, nullable=True)
    
    session = db.relationship('ChatSession', backref=db.backref('documents', lazy=True))

class MemoryContext(db.Model):
    """Model for storing conversation context and memory"""
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(Integer, db.ForeignKey('chat_session.id'), nullable=False)
    context_key = db.Column(String(100), nullable=False)
    context_value = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = db.relationship('ChatSession', backref=db.backref('memory_contexts', lazy=True))
