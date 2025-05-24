import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models import MemoryContext, ChatMessage
from app import db
from utils.logger import get_logger

logger = get_logger(__name__)

class MemoryStore:
    """Manage conversation memory and context for chat sessions"""
    
    def __init__(self):
        self.max_memory_items = 50  # Maximum memory contexts per session
        self.context_expiry_days = 7  # Memory expires after 7 days
        
    def get_context(self, session_id: int, context_type: str = 'conversation') -> List[Dict[str, Any]]:
        """Retrieve conversation context for a session"""
        try:
            # Get recent chat messages for conversation context
            if context_type == 'conversation':
                return self._get_conversation_context(session_id)
            
            # Get specific memory contexts
            memory_contexts = MemoryContext.query.filter_by(
                session_id=session_id,
                context_key=context_type
            ).order_by(MemoryContext.updated_at.desc()).limit(10).all()
            
            contexts = []
            for context in memory_contexts:
                try:
                    value = json.loads(context.context_value)
                    contexts.append({
                        'type': context.context_key,
                        'value': value,
                        'updated_at': context.updated_at.isoformat()
                    })
                except json.JSONDecodeError:
                    # Handle plain text values
                    contexts.append({
                        'type': context.context_key,
                        'value': context.context_value,
                        'updated_at': context.updated_at.isoformat()
                    })
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error retrieving context for session {session_id}: {e}")
            return []
    
    def update_memory(self, session_id: int, user_message: str, ai_response: str) -> None:
        """Update conversation memory with new interaction"""
        try:
            # Store conversation summary if it's getting long
            message_count = ChatMessage.query.filter_by(session_id=session_id).count()
            
            if message_count > 20 and message_count % 10 == 0:
                self._create_conversation_summary(session_id)
            
            # Extract and store key information from the conversation
            self._extract_and_store_entities(session_id, user_message, ai_response)
            
            # Update last activity
            self._update_last_activity(session_id)
            
        except Exception as e:
            logger.error(f"Error updating memory for session {session_id}: {e}")
    
    def store_context(self, session_id: int, context_key: str, context_value: Any) -> None:
        """Store specific context information"""
        try:
            # Convert value to JSON if it's not a string
            if isinstance(context_value, (dict, list)):
                value_str = json.dumps(context_value, ensure_ascii=False)
            else:
                value_str = str(context_value)
            
            # Check if context already exists
            existing_context = MemoryContext.query.filter_by(
                session_id=session_id,
                context_key=context_key
            ).first()
            
            if existing_context:
                existing_context.context_value = value_str
                existing_context.updated_at = datetime.utcnow()
            else:
                new_context = MemoryContext(
                    session_id=session_id,
                    context_key=context_key,
                    context_value=value_str
                )
                db.session.add(new_context)
            
            db.session.commit()
            
            # Clean up old contexts if limit exceeded
            self._cleanup_old_contexts(session_id)
            
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            db.session.rollback()
    
    def get_memory_summary(self, session_id: int) -> Dict[str, Any]:
        """Get a summary of stored memory for a session"""
        try:
            summary = {
                'conversation_length': ChatMessage.query.filter_by(session_id=session_id).count(),
                'memory_contexts': MemoryContext.query.filter_by(session_id=session_id).count(),
                'recent_topics': self._get_recent_topics(session_id),
                'key_entities': self._get_key_entities(session_id),
                'last_activity': self._get_last_activity(session_id)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting memory summary: {e}")
            return {}
    
    def clear_memory(self, session_id: int, context_type: str = None) -> None:
        """Clear memory for a session"""
        try:
            if context_type:
                # Clear specific context type
                MemoryContext.query.filter_by(
                    session_id=session_id,
                    context_key=context_type
                ).delete()
            else:
                # Clear all memory contexts (but keep chat messages)
                MemoryContext.query.filter_by(session_id=session_id).delete()
            
            db.session.commit()
            logger.info(f"Cleared memory for session {session_id}, type: {context_type or 'all'}")
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            db.session.rollback()
    
    def _get_conversation_context(self, session_id: int) -> List[Dict[str, Any]]:
        """Get recent conversation messages as context"""
        messages = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(20).all()
        
        context = []
        for msg in reversed(messages):  # Reverse to get chronological order
            context.append({
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return context
    
    def _create_conversation_summary(self, session_id: int) -> None:
        """Create a summary of the conversation for long-term memory"""
        try:
            # Get recent messages
            messages = ChatMessage.query.filter_by(
                session_id=session_id
            ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            
            if not messages:
                return
            
            # Create summary of topics discussed
            topics = []
            entities = []
            
            for msg in messages:
                content = msg.content.lower()
                
                # Extract construction-related topics
                construction_keywords = [
                    'rab', 'volume', 'biaya', 'material', 'bangunan', 'konstruksi',
                    'pajak', 'estimasi', 'perhitungan', 'gambar', 'denah', 'spesifikasi'
                ]
                
                for keyword in construction_keywords:
                    if keyword in content and keyword not in topics:
                        topics.append(keyword)
                
                # Extract numerical entities (might be important calculations)
                import re
                numbers = re.findall(r'\b\d+[\d,]*\.?\d*\b', content)
                entities.extend(numbers[:3])  # Store first 3 numbers
            
            # Store summary
            summary_data = {
                'topics': topics[:10],  # Top 10 topics
                'entities': entities[:20],  # Top 20 entities
                'timestamp': datetime.utcnow().isoformat(),
                'message_count': len(messages)
            }
            
            self.store_context(session_id, 'conversation_summary', summary_data)
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
    
    def _extract_and_store_entities(self, session_id: int, user_message: str, ai_response: str) -> None:
        """Extract and store important entities from conversation"""
        try:
            import re
            
            # Extract numbers (potentially important calculations)
            all_text = f"{user_message} {ai_response}"
            
            # Extract monetary values
            money_pattern = r'(?:Rp\.?\s*)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'
            monetary_values = re.findall(money_pattern, all_text)
            
            # Extract percentages
            percent_pattern = r'(\d+(?:\.\d+)?)\s*%'
            percentages = re.findall(percent_pattern, all_text)
            
            # Extract dimensions (e.g., 10x20, 5.5m, etc.)
            dimension_pattern = r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*m[²³]?'
            dimensions = re.findall(dimension_pattern, all_text)
            
            # Store extracted entities
            if monetary_values:
                self.store_context(session_id, 'recent_monetary_values', monetary_values[-5:])
            
            if percentages:
                self.store_context(session_id, 'recent_percentages', percentages[-5:])
            
            if dimensions:
                self.store_context(session_id, 'recent_dimensions', [d for d in dimensions if any(d)][-5:])
            
            # Extract project-related keywords
            project_keywords = [
                'proyek', 'bangunan', 'gedung', 'rumah', 'jalan', 'jembatan',
                'renovasi', 'pembangunan', 'konstruksi'
            ]
            
            found_keywords = [kw for kw in project_keywords if kw in all_text.lower()]
            if found_keywords:
                self.store_context(session_id, 'project_type_hints', found_keywords[-3:])
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
    
    def _get_recent_topics(self, session_id: int) -> List[str]:
        """Get recently discussed topics"""
        summary_context = MemoryContext.query.filter_by(
            session_id=session_id,
            context_key='conversation_summary'
        ).first()
        
        if summary_context:
            try:
                summary_data = json.loads(summary_context.context_value)
                return summary_data.get('topics', [])
            except json.JSONDecodeError:
                pass
        
        return []
    
    def _get_key_entities(self, session_id: int) -> Dict[str, List]:
        """Get key entities from memory"""
        entities = {}
        
        entity_types = ['recent_monetary_values', 'recent_percentages', 'recent_dimensions']
        
        for entity_type in entity_types:
            context = MemoryContext.query.filter_by(
                session_id=session_id,
                context_key=entity_type
            ).first()
            
            if context:
                try:
                    entities[entity_type] = json.loads(context.context_value)
                except json.JSONDecodeError:
                    entities[entity_type] = []
        
        return entities
    
    def _get_last_activity(self, session_id: int) -> Optional[str]:
        """Get timestamp of last activity"""
        last_message = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        if last_message:
            return last_message.timestamp.isoformat()
        
        return None
    
    def _update_last_activity(self, session_id: int) -> None:
        """Update last activity timestamp"""
        from models import ChatSession
        session = ChatSession.query.get(session_id)
        if session:
            session.last_activity = datetime.utcnow()
            db.session.commit()
    
    def _cleanup_old_contexts(self, session_id: int) -> None:
        """Clean up old memory contexts to stay within limits"""
        try:
            # Count current contexts
            context_count = MemoryContext.query.filter_by(session_id=session_id).count()
            
            if context_count > self.max_memory_items:
                # Delete oldest contexts
                oldest_contexts = MemoryContext.query.filter_by(
                    session_id=session_id
                ).order_by(MemoryContext.updated_at.asc()).limit(
                    context_count - self.max_memory_items
                ).all()
                
                for context in oldest_contexts:
                    db.session.delete(context)
                
                db.session.commit()
            
            # Delete expired contexts
            expiry_date = datetime.utcnow() - timedelta(days=self.context_expiry_days)
            expired_contexts = MemoryContext.query.filter(
                MemoryContext.session_id == session_id,
                MemoryContext.updated_at < expiry_date
            ).all()
            
            for context in expired_contexts:
                db.session.delete(context)
            
            if expired_contexts:
                db.session.commit()
                logger.info(f"Cleaned up {len(expired_contexts)} expired contexts for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old contexts: {e}")
            db.session.rollback()
