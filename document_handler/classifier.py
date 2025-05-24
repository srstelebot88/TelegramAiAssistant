import os
from typing import Dict, Any, Optional
from document_handler.parser_pdf import PDFParser
from document_handler.parser_docx import DocxParser
from document_handler.parser_xlsx import XlsxParser
from document_handler.image_ocr import ImageOCR
from utils.logger import get_logger

logger = get_logger(__name__)

class DocumentClassifier:
    """Classify and process different types of documents"""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.docx_parser = DocxParser()
        self.xlsx_parser = XlsxParser()
        self.image_ocr = ImageOCR()
        
        self.supported_types = {
            'pdf': self.pdf_parser.parse_pdf,
            'docx': self.docx_parser.parse_docx,
            'doc': self.docx_parser.parse_docx,  # Try with docx parser
            'xlsx': self.xlsx_parser.parse_xlsx,
            'xls': self.xlsx_parser.parse_xlsx,  # Try with xlsx parser
            'png': self.image_ocr.process_image,
            'jpg': self.image_ocr.process_image,
            'jpeg': self.image_ocr.process_image,
            'bmp': self.image_ocr.process_image,
            'tiff': self.image_ocr.process_image,
            'gif': self.image_ocr.process_image
        }
    
    def process_document(self, file_path: str, file_type: str) -> Optional[Dict[str, Any]]:
        """Process document based on its type"""
        try:
            file_type_lower = file_type.lower()
            
            if file_type_lower not in self.supported_types:
                logger.error(f"Unsupported file type: {file_type}")
                return {
                    'type': file_type,
                    'extracted_text': '',
                    'metadata': {'error': f'Unsupported file type: {file_type}'},
                    'success': False
                }
            
            # Get appropriate parser
            parser_func = self.supported_types[file_type_lower]
            
            # Process the document
            result = parser_func(file_path)
            
            if result and result.get('success', False):
                # Add classification info
                result['classification'] = self._classify_content(
                    result.get('extracted_text', ''),
                    file_type_lower
                )
                
                logger.info(f"Successfully processed {file_type} document: {file_path}")
            else:
                logger.error(f"Failed to process document: {file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                'type': file_type,
                'extracted_text': '',
                'metadata': {'error': str(e)},
                'success': False
            }
    
    def _classify_content(self, text: str, file_type: str) -> Dict[str, Any]:
        """Classify document content based on text analysis"""
        classification = {
            'document_category': 'unknown',
            'construction_relevance': 0.0,
            'tax_relevance': 0.0,
            'technical_level': 'unknown',
            'key_topics': []
        }
        
        if not text:
            return classification
        
        text_lower = text.lower()
        
        # Document categories
        category_keywords = {
            'rab': ['rencana anggaran biaya', 'rab', 'bill of quantity', 'boq'],
            'contract': ['kontrak', 'perjanjian', 'agreement', 'tender'],
            'specification': ['spesifikasi', 'specification', 'spec', 'mutu'],
            'drawing': ['gambar kerja', 'drawing', 'denah', 'potongan'],
            'report': ['laporan', 'report', 'progress', 'evaluasi'],
            'invoice': ['invoice', 'faktur', 'tagihan', 'pembayaran'],
            'permit': ['izin', 'permit', 'imb', 'surat izin']
        }
        
        # Find best matching category
        best_category = 'unknown'
        max_score = 0
        
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > max_score:
                max_score = score
                best_category = category
        
        classification['document_category'] = best_category
        
        # Construction relevance
        construction_keywords = [
            'bangunan', 'konstruksi', 'beton', 'baja', 'material',
            'volume', 'struktur', 'pondasi', 'kolom', 'balok',
            'arsitektur', 'sipil', 'mechanical', 'electrical'
        ]
        
        construction_score = sum(1 for keyword in construction_keywords if keyword in text_lower)
        classification['construction_relevance'] = min(construction_score / 10.0, 1.0)
        
        # Tax relevance
        tax_keywords = [
            'pajak', 'pph', 'ppn', 'tarif', 'withholding',
            'final', 'fiscal', 'tax', 'npwp', 'spt'
        ]
        
        tax_score = sum(1 for keyword in tax_keywords if keyword in text_lower)
        classification['tax_relevance'] = min(tax_score / 5.0, 1.0)
        
        # Technical level
        technical_indicators = [
            'sni', 'astm', 'din', 'bs', 'specification',
            'standard', 'code', 'regulation', 'procedure'
        ]
        
        technical_score = sum(1 for indicator in technical_indicators if indicator in text_lower)
        
        if technical_score >= 3:
            classification['technical_level'] = 'high'
        elif technical_score >= 1:
            classification['technical_level'] = 'medium'
        else:
            classification['technical_level'] = 'low'
        
        # Extract key topics
        all_topics = construction_keywords + tax_keywords + technical_indicators
        found_topics = [topic for topic in all_topics if topic in text_lower]
        classification['key_topics'] = list(set(found_topics))[:10]  # Limit to 10 topics
        
        return classification
    
    def get_supported_types(self) -> list:
        """Get list of supported file types"""
        return list(self.supported_types.keys())
    
    def is_supported(self, file_type: str) -> bool:
        """Check if file type is supported"""
        return file_type.lower() in self.supported_types