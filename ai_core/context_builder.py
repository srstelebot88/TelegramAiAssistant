from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from models import ChatMessage, DocumentUpload, MemoryContext
from utils.logger import get_logger

logger = get_logger(__name__)

class ContextBuilder:
    """Build comprehensive context for AI conversations"""
    
    def __init__(self):
        self.max_context_length = 4000  # Maximum characters for context
        self.max_messages = 10  # Maximum messages to include
        self.max_documents = 3  # Maximum recent documents to reference
        
    def build_conversation_context(self, session_id: int, current_message: str) -> Dict[str, Any]:
        """Build comprehensive context for conversation"""
        context = {
            'conversation_history': self._get_conversation_history(session_id),
            'recent_documents': self._get_recent_documents(session_id),
            'user_preferences': self._get_user_preferences(session_id),
            'session_summary': self._get_session_summary(session_id),
            'current_message': current_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return context
    
    def build_document_context(self, session_id: int, document_id: int) -> Dict[str, Any]:
        """Build context for document analysis"""
        document = DocumentUpload.query.get(document_id)
        if not document:
            return {}
        
        context = {
            'document_info': {
                'id': document.id,
                'filename': document.filename,
                'type': document.file_type,
                'size': document.file_size,
                'upload_date': document.upload_timestamp.isoformat()
            },
            'related_documents': self._get_related_documents(session_id, document.file_type),
            'user_context': self._get_user_preferences(session_id),
            'previous_analysis': document.processing_result if document.processed else None
        }
        
        return context
    
    def build_calculation_context(self, session_id: int, calc_type: str, input_data: Dict) -> Dict[str, Any]:
        """Build context for calculations"""
        context = {
            'calculation_type': calc_type,
            'input_data': input_data,
            'user_preferences': self._get_user_preferences(session_id),
            'recent_calculations': self._get_recent_calculations(session_id, calc_type),
            'related_documents': self._get_calculation_relevant_documents(session_id),
            'market_context': self._get_market_context()
        }
        
        return context
    
    def extract_entities_from_message(self, message: str) -> Dict[str, List[str]]:
        """Extract relevant entities from a message"""
        import re
        
        entities = {
            'monetary_values': [],
            'dimensions': [],
            'percentages': [],
            'materials': [],
            'locations': [],
            'dates': [],
            'project_types': []
        }
        
        # Extract monetary values
        money_patterns = [
            r'(?:Rp\.?\s*)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            r'(\d+)\s*(?:juta|miliar|ribu)',
            r'(\d+(?:\.\d+)?)\s*(?:M|K|B)'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            entities['monetary_values'].extend(matches)
        
        # Extract dimensions
        dimension_patterns = [
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*m[²³]?',
            r'(\d+(?:\.\d+)?)\s*(?:meter|m)\s*(?:persegi|kubik)?'
        ]
        
        for pattern in dimension_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            entities['dimensions'].extend([match for match in matches if match])
        
        # Extract percentages
        percent_pattern = r'(\d+(?:\.\d+)?)\s*%'
        entities['percentages'] = re.findall(percent_pattern, message)
        
        # Extract materials
        material_keywords = [
            'beton', 'semen', 'pasir', 'batu', 'besi', 'baja', 'kayu', 'keramik',
            'cat', 'genteng', 'pipa', 'kabel', 'bata', 'hebel', 'gypsum'
        ]
        
        for material in material_keywords:
            if material.lower() in message.lower():
                entities['materials'].append(material)
        
        # Extract project types
        project_keywords = [
            'rumah', 'gedung', 'kantor', 'sekolah', 'rumah sakit', 'jalan',
            'jembatan', 'apartemen', 'villa', 'ruko', 'warehouse', 'pabrik'
        ]
        
        for project_type in project_keywords:
            if project_type.lower() in message.lower():
                entities['project_types'].append(project_type)
        
        # Extract locations (Indonesian cities/regions)
        location_keywords = [
            'jakarta', 'surabaya', 'bandung', 'medan', 'bekasi', 'tangerang',
            'depok', 'semarang', 'palembang', 'makassar', 'yogyakarta', 'solo'
        ]
        
        for location in location_keywords:
            if location.lower() in message.lower():
                entities['locations'].append(location)
        
        # Extract dates
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            entities['dates'].extend([' '.join(match) for match in matches])
        
        return entities
    
    def _get_conversation_history(self, session_id: int) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        messages = ChatMessage.query.filter_by(
            session_id=session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(self.max_messages).all()
        
        history = []
        total_length = 0
        
        for msg in reversed(messages):  # Reverse to get chronological order
            msg_data = {
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            
            # Check if adding this message would exceed length limit
            msg_length = len(msg.content)
            if total_length + msg_length > self.max_context_length:
                break
            
            history.append(msg_data)
            total_length += msg_length
        
        return history
    
    def _get_recent_documents(self, session_id: int) -> List[Dict[str, Any]]:
        """Get information about recent documents"""
        documents = DocumentUpload.query.filter_by(
            session_id=session_id
        ).order_by(DocumentUpload.upload_timestamp.desc()).limit(self.max_documents).all()
        
        doc_info = []
        for doc in documents:
            doc_info.append({
                'id': doc.id,
                'filename': doc.filename,
                'type': doc.file_type,
                'upload_date': doc.upload_timestamp.isoformat(),
                'processed': doc.processed,
                'summary': doc.processing_result[:200] if doc.processing_result else None
            })
        
        return doc_info
    
    def _get_user_preferences(self, session_id: int) -> Dict[str, Any]:
        """Get user preferences from memory contexts"""
        preferences = {}
        
        # Get preferences from memory contexts
        pref_contexts = MemoryContext.query.filter(
            MemoryContext.session_id == session_id,
            MemoryContext.context_key.like('pref_%')
        ).all()
        
        for context in pref_contexts:
            key = context.context_key.replace('pref_', '')
            try:
                import json
                preferences[key] = json.loads(context.context_value)
            except:
                preferences[key] = context.context_value
        
        # Set defaults if not found
        preferences.setdefault('currency', 'IDR')
        preferences.setdefault('units', 'metric')
        preferences.setdefault('language', 'id')
        preferences.setdefault('detail_level', 'medium')
        
        return preferences
    
    def _get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Get summary of the current session"""
        from models import ChatSession
        
        session = ChatSession.query.get(session_id)
        if not session:
            return {}
        
        message_count = ChatMessage.query.filter_by(session_id=session_id).count()
        doc_count = DocumentUpload.query.filter_by(session_id=session_id).count()
        
        # Get time since last activity
        time_since_start = datetime.utcnow() - session.created_at
        time_since_activity = datetime.utcnow() - session.last_activity
        
        return {
            'session_duration': str(time_since_start),
            'time_since_activity': str(time_since_activity),
            'message_count': message_count,
            'document_count': doc_count,
            'user_info': {
                'first_name': session.first_name,
                'username': session.username
            }
        }
    
    def _get_related_documents(self, session_id: int, file_type: str) -> List[Dict[str, Any]]:
        """Get documents of similar type"""
        documents = DocumentUpload.query.filter_by(
            session_id=session_id,
            file_type=file_type
        ).order_by(DocumentUpload.upload_timestamp.desc()).limit(3).all()
        
        return [{
            'id': doc.id,
            'filename': doc.filename,
            'upload_date': doc.upload_timestamp.isoformat()
        } for doc in documents]
    
    def _get_recent_calculations(self, session_id: int, calc_type: str) -> List[Dict[str, Any]]:
        """Get recent calculations of the same type"""
        calc_contexts = MemoryContext.query.filter(
            MemoryContext.session_id == session_id,
            MemoryContext.context_key == f'calc_{calc_type}'
        ).order_by(MemoryContext.updated_at.desc()).limit(3).all()
        
        calculations = []
        for context in calc_contexts:
            try:
                import json
                calc_data = json.loads(context.context_value)
                calculations.append({
                    'date': context.updated_at.isoformat(),
                    'data': calc_data
                })
            except:
                pass
        
        return calculations
    
    def _get_calculation_relevant_documents(self, session_id: int) -> List[Dict[str, Any]]:
        """Get documents relevant for calculations"""
        # Look for spreadsheets and PDFs that might contain calculation data
        relevant_types = ['xlsx', 'xls', 'pdf']
        
        documents = DocumentUpload.query.filter(
            DocumentUpload.session_id == session_id,
            DocumentUpload.file_type.in_(relevant_types),
            DocumentUpload.processed == True
        ).order_by(DocumentUpload.upload_timestamp.desc()).limit(3).all()
        
        return [{
            'id': doc.id,
            'filename': doc.filename,
            'type': doc.file_type,
            'summary': doc.processing_result[:100] if doc.processing_result else None
        } for doc in documents]
    
    def _get_market_context(self) -> Dict[str, Any]:
        """Get current market context for calculations"""
        # This would ideally fetch real market data
        # For now, return static context
        return {
            'currency': 'IDR',
            'inflation_rate': 3.5,  # Example rate
            'construction_index': 105.2,  # Example index
            'last_updated': datetime.utcnow().isoformat(),
            'note': 'Market data would be fetched from external sources in production'
        }
