import yaml
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class PromptEngine:
    """Engine for building and managing AI prompts for construction and tax analysis"""
    
    def __init__(self):
        self.system_prompts = self._load_system_prompts()
        self.conversation_context_limit = 10  # Last 10 messages
        
    def build_conversation_prompt(self, user_message: str, context: List[Dict] = None) -> str:
        """Build prompt for general conversation"""
        system_prompt = self.system_prompts.get('conversation', self._get_default_conversation_prompt())
        
        # Build context from previous messages
        context_text = ""
        if context:
            context_text = self._format_conversation_context(context)
        
        prompt = f"""{system_prompt}

{context_text}

Pertanyaan User: {user_message}

Jawaban Assistant:"""
        
        return prompt
    
    def build_document_analysis_prompt(self, document_content: str, document_type: str, 
                                     analysis_type: str = "general") -> str:
        """Build prompt for document analysis"""
        base_prompt = self.system_prompts.get('document_analysis', self._get_default_document_prompt())
        
        type_specific_instructions = {
            'pdf': "Fokus pada ekstraksi data teknis, spesifikasi, dan angka-angka penting.",
            'docx': "Analisis kontrak, syarat kerja, dan ketentuan teknis.",
            'xlsx': "Ekstrak data numerik, tabel biaya, dan perhitungan volume.",
            'image': "Lakukan OCR dan identifikasi elemen teknis dari gambar."
        }
        
        specific_instruction = type_specific_instructions.get(document_type, "Analisis konten dokumen secara umum.")
        
        prompt = f"""{base_prompt}

Jenis Dokumen: {document_type.upper()}
Instruksi Khusus: {specific_instruction}

Konten Dokumen:
{document_content[:4000]}  # Limit content to avoid token overflow

Berikan analisis yang mencakup:
1. Ringkasan konten utama
2. Data teknis yang ditemukan
3. Estimasi biaya (jika ada)
4. Rekomendasi tindak lanjut

Analisis:"""
        
        return prompt
    
    def build_calculation_prompt(self, calc_type: str, input_data: Dict[str, Any]) -> str:
        """Build prompt for construction calculations"""
        calculation_prompts = {
            'volume': self._get_volume_calculation_prompt(),
            'cost': self._get_cost_calculation_prompt(),
            'tax': self._get_tax_calculation_prompt(),
            'material': self._get_material_calculation_prompt()
        }
        
        base_prompt = calculation_prompts.get(calc_type, "Lakukan perhitungan konstruksi berdasarkan data yang diberikan.")
        
        # Format input data
        data_text = self._format_input_data(input_data)
        
        prompt = f"""{base_prompt}

Data Input:
{data_text}

Silakan lakukan perhitungan dan berikan hasil dalam format yang jelas dan terstruktur.

Perhitungan:"""
        
        return prompt
    
    def build_summary_prompt(self, content: str, summary_type: str = "smart") -> str:
        """Build prompt for creating summaries"""
        summary_prompts = {
            'smart': "Buat ringkasan cerdas yang mencakup poin-poin kunci dan actionable insights.",
            'technical': "Buat ringkasan teknis yang fokus pada spesifikasi dan data numerik.",
            'executive': "Buat ringkasan eksekutif untuk pengambilan keputusan.",
            'cost': "Buat ringkasan fokus pada aspek biaya dan anggaran."
        }
        
        instruction = summary_prompts.get(summary_type, summary_prompts['smart'])
        
        prompt = f"""Anda adalah expert dalam konstruksi dan pajak. {instruction}

Konten untuk diringkas:
{content[:3000]}

Format ringkasan:
1. **Poin Utama** (bullet points)
2. **Data Kunci** (angka, spesifikasi)
3. **Rekomendasi** (action items)
4. **Perhatian Khusus** (risks, compliance)

Ringkasan:"""
        
        return prompt
    
    def build_ocr_analysis_prompt(self, ocr_text: str, image_type: str = "technical") -> str:
        """Build prompt for analyzing OCR results from technical images"""
        prompt = f"""Anda adalah expert dalam membaca dan menganalisis dokumen teknis konstruksi. 
Analisis hasil OCR berikut dari gambar teknis:

Jenis Gambar: {image_type}
Hasil OCR:
{ocr_text}

Tugas Anda:
1. Identifikasi jenis dokumen (denah, potongan, detail, RAB, dll)
2. Ekstrak informasi teknis penting (dimensi, material, spesifikasi)
3. Identifikasi data numerik (ukuran, kuantitas, harga)
4. Deteksi standar atau kode yang digunakan
5. Berikan interpretasi dan rekomendasi

Analisis:"""
        
        return prompt
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from configuration"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config.get('prompts', {})
        except Exception as e:
            logger.warning(f"Failed to load prompts from config: {e}")
            return {}
    
    def _get_default_conversation_prompt(self) -> str:
        """Default conversation system prompt"""
        return """Anda adalah AI Assistant yang ahli dalam bidang konstruksi dan perpajakan Indonesia. 

Keahlian Anda meliputi:
- Analisis dokumen konstruksi (RAB, gambar kerja, spesifikasi)
- Perhitungan volume, biaya, dan estimasi proyek
- Perpajakan konstruksi (PPh Final, PPN, dll)
- Standar konstruksi Indonesia (SNI)
- Regulasi PUPR dan peraturan terkait

Gaya komunikasi:
- Profesional namun ramah
- Gunakan istilah teknis yang tepat
- Berikan penjelasan yang jelas dan actionable
- Sertakan dasar hukum/standar jika relevan
- Gunakan emoji yang sesuai untuk memperjelas

Selalu berikan jawaban yang akurat, praktis, dan sesuai dengan kondisi Indonesia."""
    
    def _get_default_document_prompt(self) -> str:
        """Default document analysis prompt"""
        return """Anda adalah expert dalam analisis dokumen konstruksi dan perpajakan. 
Analisis dokumen yang diberikan dengan teliti dan berikan insight yang berguna."""
    
    def _get_volume_calculation_prompt(self) -> str:
        """Prompt for volume calculations"""
        return """Anda adalah quantity surveyor expert. Hitung volume berdasarkan data yang diberikan.
Gunakan rumus standar konstruksi dan berikan breakdown perhitungan yang jelas.
Sertakan satuan yang tepat dan asumsi yang digunakan."""
    
    def _get_cost_calculation_prompt(self) -> str:
        """Prompt for cost calculations"""
        return """Anda adalah cost estimator expert. Hitung estimasi biaya berdasarkan data volume dan harga satuan.
Berikan breakdown biaya material, upah, dan overhead.
Gunakan harga pasar terkini di Indonesia dan sertakan markup yang wajar."""
    
    def _get_tax_calculation_prompt(self) -> str:
        """Prompt for tax calculations"""
        return """Anda adalah tax consultant expert untuk sektor konstruksi.
Hitung pajak yang terutang berdasarkan peraturan perpajakan Indonesia terkini.
Jelaskan jenis pajak, tarif, dan cara perhitungannya."""
    
    def _get_material_calculation_prompt(self) -> str:
        """Prompt for material calculations"""
        return """Anda adalah material quantity expert. Hitung kebutuhan material berdasarkan spesifikasi teknis.
Berikan daftar material lengkap dengan kuantitas, satuan, dan estimasi harga.
Sertakan allowance untuk waste dan toleransi."""
    
    def _format_conversation_context(self, context: List[Dict]) -> str:
        """Format conversation history for context"""
        if not context:
            return ""
        
        formatted_context = "Riwayat Percakapan:\n"
        
        # Get last N messages
        recent_context = context[-self.conversation_context_limit:]
        
        for msg in recent_context:
            role = "User" if msg.get('type') == 'user' else "Assistant"
            content = msg.get('content', '')[:200]  # Limit content length
            formatted_context += f"{role}: {content}\n"
        
        return formatted_context + "\n"
    
    def _format_input_data(self, data: Dict[str, Any]) -> str:
        """Format input data for prompts"""
        formatted = ""
        for key, value in data.items():
            formatted += f"- {key}: {value}\n"
        return formatted
    
    def get_preset_prompts(self) -> Dict[str, str]:
        """Get available preset prompts for quick access"""
        return {
            'rab_analysis': "Analisis RAB ini dan berikan ringkasan biaya serta rekomendasi optimasi.",
            'volume_check': "Periksa perhitungan volume dalam dokumen ini dan validasi keakuratannya.",
            'tax_compliance': "Review dokumen untuk memastikan compliance dengan regulasi pajak konstruksi.",
            'cost_optimization': "Berikan rekomendasi untuk optimasi biaya tanpa mengurangi kualitas.",
            'standard_check': "Periksa kesesuaian dengan standar SNI dan regulasi PUPR.",
            'risk_assessment': "Identifikasi risiko konstruksi dan perpajakan dari dokumen ini."
        }
