from typing import Dict, Any, List, Optional
from ai_core.model_client import AIModelClient
from app.prompt_engine import PromptEngine
from utils.logger import get_logger

logger = get_logger(__name__)

class AISummarizer:
    """AI-powered summarization for documents and conversations"""
    
    def __init__(self):
        self.ai_client = AIModelClient()
        self.prompt_engine = PromptEngine()
        
    def summarize_document(self, content: str, document_type: str = "general", 
                          summary_type: str = "smart") -> Optional[Dict[str, Any]]:
        """Create AI summary of document content"""
        try:
            # Build appropriate prompt
            prompt = self.prompt_engine.build_summary_prompt(content, summary_type)
            
            # Get AI response
            ai_response = self.ai_client.generate_response(prompt)
            
            if not ai_response:
                return None
            
            # Parse and structure the summary
            summary = self._parse_summary_response(ai_response, document_type)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating document summary: {e}")
            return None
    
    def summarize_conversation(self, messages: List[Dict[str, Any]], 
                             focus: str = "key_points") -> Optional[Dict[str, Any]]:
        """Create summary of conversation history"""
        try:
            # Format conversation for summarization
            conversation_text = self._format_conversation_for_summary(messages)
            
            # Build prompt based on focus
            if focus == "key_points":
                prompt = f"""Buat ringkasan poin-poin kunci dari percakapan berikut:

{conversation_text}

Format ringkasan:
1. **Topik Utama**: (topik yang dibahas)
2. **Keputusan/Kesimpulan**: (hasil atau keputusan penting)
3. **Action Items**: (tindakan yang perlu dilakukan)
4. **Data Penting**: (angka, spesifikasi, dll)

Ringkasan:"""
            
            elif focus == "technical":
                prompt = f"""Buat ringkasan teknis dari percakapan konstruksi berikut:

{conversation_text}

Fokus pada:
- Spesifikasi teknis
- Perhitungan dan angka
- Material dan metode
- Standar yang dirujuk

Ringkasan Teknis:"""
            
            elif focus == "financial":
                prompt = f"""Buat ringkasan finansial dari percakapan berikut:

{conversation_text}

Fokus pada:
- Estimasi biaya
- Perhitungan pajak
- Harga material
- Budget dan anggaran

Ringkasan Finansial:"""
            
            else:
                prompt = self.prompt_engine.build_summary_prompt(conversation_text, "smart")
            
            # Get AI response
            ai_response = self.ai_client.generate_response(prompt)
            
            if not ai_response:
                return None
            
            return {
                'summary': ai_response,
                'focus': focus,
                'message_count': len(messages),
                'created_at': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
            return None
    
    def extract_key_data(self, content: str, data_type: str = "construction") -> Optional[Dict[str, Any]]:
        """Extract key data points from content"""
        try:
            data_extraction_prompts = {
                'construction': """Ekstrak data teknis konstruksi dari teks berikut:

{content}

Ekstrak dalam format JSON:
{{
    "dimensions": ["10x20m", "tinggi 3.5m"],
    "materials": [{{"name": "beton", "quantity": "50m³", "price": "800000"}}, ...],
    "costs": [{{"item": "material", "amount": "500000000"}}, ...],
    "specifications": ["mutu K-300", "besi 10mm", ...],
    "areas": [{{"type": "lantai", "area": "200m²"}}, ...]
}}

Data:""",
                
                'financial': """Ekstrak data finansial dari teks berikut:

{content}

Ekstrak dalam format JSON:
{{
    "total_costs": [{{"item": "material", "amount": 500000000}}, ...],
    "taxes": [{{"type": "PPh Final", "rate": "2%", "amount": 10000000}}, ...],
    "percentages": [{{"context": "markup", "value": "15%"}}, ...],
    "currencies": ["IDR", "USD"],
    "payment_terms": ["30% down payment", "70% progress"]
}}

Data:""",
                
                'technical': """Ekstrak spesifikasi teknis dari teks berikut:

{content}

Ekstrak dalam format JSON:
{{
    "standards": ["SNI 03-2847-2013", "ASTM C39", ...],
    "materials": [{{"name": "beton", "grade": "K-300", "spec": "fc' 25 MPa"}}, ...],
    "dimensions": [{{"element": "kolom", "size": "40x40cm"}}, ...],
    "methods": ["cast in place", "precast", ...],
    "equipment": ["concrete pump", "tower crane", ...]
}}

Data:"""
            }
            
            prompt_template = data_extraction_prompts.get(data_type, data_extraction_prompts['construction'])
            prompt = prompt_template.format(content=content[:3000])  # Limit content length
            
            # Get AI response
            ai_response = self.ai_client.generate_response(prompt)
            
            if not ai_response:
                return None
            
            # Try to parse JSON response
            try:
                import json
                extracted_data = json.loads(ai_response)
                return {
                    'data_type': data_type,
                    'extracted_data': extracted_data,
                    'raw_response': ai_response,
                    'created_at': self._get_current_timestamp()
                }
            except json.JSONDecodeError:
                # If not JSON, return as structured text
                return {
                    'data_type': data_type,
                    'extracted_data': ai_response,
                    'format': 'text',
                    'created_at': self._get_current_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Error extracting key data: {e}")
            return None
    
    def create_executive_summary(self, project_data: Dict[str, Any]) -> Optional[str]:
        """Create executive summary for project data"""
        try:
            prompt = f"""Buat ringkasan eksekutif untuk proyek konstruksi berdasarkan data berikut:

Data Proyek:
{self._format_project_data(project_data)}

Format Ringkasan Eksekutif:

**RINGKASAN EKSEKUTIF PROYEK**

**1. Overview Proyek**
- Jenis dan skala proyek
- Lokasi dan timeline

**2. Aspek Teknis Utama**
- Spesifikasi kunci
- Metode konstruksi
- Material utama

**3. Aspek Finansial**
- Total estimasi biaya
- Breakdown biaya utama
- Struktur pembayaran

**4. Risiko dan Mitigasi**
- Risiko utama yang teridentifikasi
- Strategi mitigasi

**5. Rekomendasi**
- Action items prioritas
- Pertimbangan khusus

Ringkasan Eksekutif:"""
            
            ai_response = self.ai_client.generate_response(prompt)
            return ai_response
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            return None
    
    def _parse_summary_response(self, response: str, document_type: str) -> Dict[str, Any]:
        """Parse AI summary response into structured format"""
        # Try to identify different sections in the response
        sections = {}
        
        # Common section headers to look for
        section_patterns = [
            r'\*\*([^*]+)\*\*:?\s*([^\*]+?)(?=\*\*|$)',
            r'(\d+\.\s*[^:]+):?\s*([^\d]+?)(?=\d+\.|$)',
            r'([A-Z][^:]+):?\s*([^A-Z]+?)(?=[A-Z]|$)'
        ]
        
        import re
        for pattern in section_patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            for title, content in matches:
                clean_title = title.strip().lower().replace(' ', '_')
                sections[clean_title] = content.strip()
        
        # If no sections found, treat as single summary
        if not sections:
            sections['summary'] = response
        
        return {
            'type': document_type,
            'sections': sections,
            'full_text': response,
            'created_at': self._get_current_timestamp(),
            'word_count': len(response.split())
        }
    
    def _format_conversation_for_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation messages for summarization"""
        formatted = ""
        
        for msg in messages[-20:]:  # Last 20 messages
            role = "User" if msg.get('type') == 'user' else "Assistant"
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            formatted += f"\n[{role}] {content}\n"
        
        return formatted
    
    def _format_project_data(self, data: Dict[str, Any]) -> str:
        """Format project data for executive summary"""
        formatted = ""
        
        for key, value in data.items():
            if isinstance(value, dict):
                formatted += f"\n{key.title()}:\n"
                for sub_key, sub_value in value.items():
                    formatted += f"  - {sub_key}: {sub_value}\n"
            elif isinstance(value, list):
                formatted += f"\n{key.title()}:\n"
                for item in value:
                    formatted += f"  - {item}\n"
            else:
                formatted += f"\n{key.title()}: {value}\n"
        
        return formatted
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
