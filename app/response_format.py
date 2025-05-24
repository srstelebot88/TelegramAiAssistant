import re
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ResponseFormatter:
    """Format AI responses and document analysis results for Telegram"""
    
    def __init__(self):
        self.max_message_length = 4096  # Telegram message limit
        
    def format_message(self, text: str) -> str:
        """Format general AI response for Telegram"""
        if not text:
            return "Maaf, tidak ada respons yang dapat dihasilkan."
        
        # Clean and format text
        formatted = self._clean_text(text)
        
        # Add emojis for better UX
        formatted = self._add_contextual_emojis(formatted)
        
        # Ensure message length is within limits
        if len(formatted) > self.max_message_length:
            formatted = formatted[:self.max_message_length-100] + "\n\n✂️ *Pesan dipotong karena terlalu panjang...*"
        
        return formatted
    
    def format_document_analysis(self, analysis_result: Dict[str, Any]) -> str:
        """Format document analysis results"""
        if not analysis_result:
            return "❌ Gagal menganalisis dokumen."
        
        document_type = analysis_result.get('type', 'unknown')
        extracted_text = analysis_result.get('extracted_text', '')
        metadata = analysis_result.get('metadata', {})
        
        # Format based on document type
        if document_type == 'pdf':
            return self._format_pdf_analysis(extracted_text, metadata)
        elif document_type == 'docx':
            return self._format_docx_analysis(extracted_text, metadata)
        elif document_type == 'xlsx':
            return self._format_xlsx_analysis(analysis_result)
        elif document_type in ['png', 'jpg', 'jpeg']:
            return self._format_image_ocr_analysis(extracted_text, metadata)
        else:
            return self._format_generic_analysis(extracted_text, metadata)
    
    def format_calculation_result(self, calc_type: str, result: Dict[str, Any]) -> str:
        """Format construction calculation results"""
        if calc_type == 'volume':
            return self._format_volume_calculation(result)
        elif calc_type == 'cost':
            return self._format_cost_calculation(result)
        elif calc_type == 'tax':
            return self._format_tax_calculation(result)
        elif calc_type == 'material':
            return self._format_material_calculation(result)
        else:
            return "❌ Tipe perhitungan tidak dikenali."
    
    def format_error_message(self, error_type: str, details: str = "") -> str:
        """Format error messages"""
        error_messages = {
            'file_too_large': "❌ File terlalu besar. Maksimal 50MB.",
            'unsupported_format': "❌ Format file tidak didukung.",
            'processing_failed': "❌ Gagal memproses dokumen.",
            'ai_error': "❌ Terjadi kesalahan pada AI processing.",
            'network_error': "❌ Koneksi bermasalah. Coba lagi nanti.",
            'quota_exceeded': "❌ Kuota API tercapai. Coba lagi nanti."
        }
        
        base_message = error_messages.get(error_type, "❌ Terjadi kesalahan tidak diketahui.")
        
        if details:
            return f"{base_message}\n\n🔍 Detail: {details}"
        
        return base_message
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common formatting issues
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Escape special Telegram markdown characters
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _add_contextual_emojis(self, text: str) -> str:
        """Add relevant emojis based on content"""
        # Construction related keywords
        construction_keywords = {
            'volume': '📐',
            'biaya': '💰',
            'material': '🧱',
            'bangunan': '🏗️',
            'konstruksi': '🏗️',
            'pajak': '🧮',
            'estimasi': '📊',
            'perhitungan': '🧮',
            'analisis': '🔍',
            'dokumen': '📄'
        }
        
        for keyword, emoji in construction_keywords.items():
            if keyword.lower() in text.lower() and emoji not in text:
                text = f"{emoji} {text}"
                break
        
        return text
    
    def _format_pdf_analysis(self, text: str, metadata: Dict) -> str:
        """Format PDF analysis result"""
        page_count = metadata.get('pages', 'unknown')
        file_size = metadata.get('size', 'unknown')
        
        result = f"""📄 **Analisis Dokumen PDF**

📊 **Informasi File:**
• Halaman: {page_count}
• Ukuran: {file_size}

📝 **Konten Terdeteksi:**
{text[:1000]}{'...' if len(text) > 1000 else ''}

✅ **Status**: Berhasil dianalisis"""
        
        return result
    
    def _format_docx_analysis(self, text: str, metadata: Dict) -> str:
        """Format DOCX analysis result"""
        word_count = metadata.get('words', 'unknown')
        
        result = f"""📝 **Analisis Dokumen DOCX**

📊 **Informasi:**
• Jumlah kata: {word_count}

📄 **Konten:**
{text[:1000]}{'...' if len(text) > 1000 else ''}

✅ **Status**: Berhasil dianalisis"""
        
        return result
    
    def _format_xlsx_analysis(self, analysis_result: Dict) -> str:
        """Format XLSX analysis result"""
        sheets = analysis_result.get('sheets', {})
        sheet_count = len(sheets)
        
        result = f"""📊 **Analisis Spreadsheet XLSX**

📈 **Informasi:**
• Jumlah sheet: {sheet_count}
• Sheet: {', '.join(sheets.keys())}

📋 **Data Terdeteksi:**"""
        
        for sheet_name, data in sheets.items():
            if isinstance(data, list) and data:
                result += f"\n\n**{sheet_name}:**"
                for i, row in enumerate(data[:5]):  # Show first 5 rows
                    result += f"\n{i+1}. {' | '.join(map(str, row[:5]))}"
                if len(data) > 5:
                    result += f"\n... dan {len(data)-5} baris lainnya"
        
        result += "\n\n✅ **Status**: Berhasil dianalisis"
        return result
    
    def _format_image_ocr_analysis(self, text: str, metadata: Dict) -> str:
        """Format OCR analysis result"""
        confidence = metadata.get('confidence', 'unknown')
        image_size = metadata.get('size', 'unknown')
        
        result = f"""🖼️ **Analisis OCR Gambar**

📊 **Informasi:**
• Ukuran: {image_size}
• Confidence: {confidence}

📝 **Teks Terdeteksi:**
{text[:1000] if text else 'Tidak ada teks terdeteksi'}

✅ **Status**: {'Berhasil' if text else 'Tidak ada teks'}"""
        
        return result
    
    def _format_generic_analysis(self, text: str, metadata: Dict) -> str:
        """Format generic document analysis"""
        return f"""📄 **Analisis Dokumen**

📝 **Konten:**
{text[:1000]}{'...' if len(text) > 1000 else ''}

✅ **Status**: Berhasil dianalisis"""
    
    def _format_volume_calculation(self, result: Dict) -> str:
        """Format volume calculation result"""
        volume = result.get('volume', 0)
        unit = result.get('unit', 'm³')
        breakdown = result.get('breakdown', {})
        
        formatted = f"""📐 **Perhitungan Volume**

📊 **Hasil:**
• Total Volume: {volume:,.2f} {unit}

📋 **Rincian:**"""
        
        for item, value in breakdown.items():
            formatted += f"\n• {item}: {value}"
        
        return formatted
    
    def _format_cost_calculation(self, result: Dict) -> str:
        """Format cost calculation result"""
        total_cost = result.get('total_cost', 0)
        breakdown = result.get('breakdown', {})
        
        formatted = f"""💰 **Estimasi Biaya**

💵 **Total**: Rp {total_cost:,.0f}

📋 **Rincian:**"""
        
        for category, amount in breakdown.items():
            formatted += f"\n• {category}: Rp {amount:,.0f}"
        
        return formatted
    
    def _format_tax_calculation(self, result: Dict) -> str:
        """Format tax calculation result"""
        base_amount = result.get('base_amount', 0)
        tax_amount = result.get('tax_amount', 0)
        tax_rate = result.get('tax_rate', 0)
        
        formatted = f"""🧮 **Perhitungan Pajak**

💰 **Dasar Pengenaan**: Rp {base_amount:,.0f}
📊 **Tarif Pajak**: {tax_rate}%
🧮 **Pajak Terutang**: Rp {tax_amount:,.0f}

💵 **Total Bayar**: Rp {base_amount + tax_amount:,.0f}"""
        
        return formatted
    
    def _format_material_calculation(self, result: Dict) -> str:
        """Format material calculation result"""
        materials = result.get('materials', {})
        total_cost = result.get('total_cost', 0)
        
        formatted = f"""📐 **Perhitungan Material**

💰 **Total Biaya Material**: Rp {total_cost:,.0f}

📋 **Rincian Material:**"""
        
        for material, details in materials.items():
            quantity = details.get('quantity', 0)
            unit = details.get('unit', '')
            price = details.get('price', 0)
            total = details.get('total', 0)
            
            formatted += f"\n• {material}: {quantity} {unit} @ Rp {price:,.0f} = Rp {total:,.0f}"
        
        return formatted
