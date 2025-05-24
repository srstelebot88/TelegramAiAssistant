import PyPDF2
import io
import os
from typing import Dict, Any, Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)

class PDFParser:
    """Parser for PDF documents"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    def parse_pdf(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse PDF file and extract text and metadata"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"PDF file not found: {file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"PDF file too large: {file_size} bytes")
                return None
            
            result = {
                'type': 'pdf',
                'extracted_text': '',
                'metadata': {
                    'pages': 0,
                    'size': file_size,
                    'file_path': file_path
                },
                'pages_content': [],
                'success': True
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get metadata
                result['metadata']['pages'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    result['metadata'].update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                    })
                
                # Extract text from each page
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            page_text = page_text.strip()
                            full_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                            
                            result['pages_content'].append({
                                'page_number': page_num + 1,
                                'text': page_text,
                                'char_count': len(page_text)
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                        result['pages_content'].append({
                            'page_number': page_num + 1,
                            'text': f"[Error extracting page: {str(e)}]",
                            'char_count': 0
                        })
                
                result['extracted_text'] = full_text.strip()
                result['metadata']['total_characters'] = len(result['extracted_text'])
                result['metadata']['total_words'] = len(result['extracted_text'].split())
                
                # Analyze content type
                content_analysis = self._analyze_pdf_content(result['extracted_text'])
                result['content_analysis'] = content_analysis
                
                logger.info(f"Successfully parsed PDF: {file_path}, {result['metadata']['pages']} pages, {result['metadata']['total_characters']} characters")
                
                return result
                
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return {
                'type': 'pdf',
                'extracted_text': '',
                'metadata': {'error': str(e)},
                'success': False
            }
    
    def extract_tables(self, file_path: str) -> Optional[List[List[str]]]:
        """Extract tables from PDF (basic implementation)"""
        try:
            # This is a basic implementation
            # For more advanced table extraction, consider using tabula-py or camelot
            
            result = self.parse_pdf(file_path)
            if not result or not result['success']:
                return None
            
            text = result['extracted_text']
            tables = self._extract_tables_from_text(text)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            return None
    
    def extract_images_info(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Extract information about images in PDF"""
        try:
            images_info = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                images_info.append({
                                    'page': page_num + 1,
                                    'name': obj,
                                    'width': xObject[obj].get('/Width', 'unknown'),
                                    'height': xObject[obj].get('/Height', 'unknown'),
                                    'bits_per_component': xObject[obj].get('/BitsPerComponent', 'unknown'),
                                    'color_space': str(xObject[obj].get('/ColorSpace', 'unknown'))
                                })
            
            return images_info
            
        except Exception as e:
            logger.error(f"Error extracting image info from PDF: {e}")
            return None
    
    def _analyze_pdf_content(self, text: str) -> Dict[str, Any]:
        """Analyze PDF content to determine document type and extract key information"""
        import re
        
        analysis = {
            'document_type': 'unknown',
            'keywords_found': [],
            'numbers_found': [],
            'currency_amounts': [],
            'confidence_score': 0.0
        }
        
        text_lower = text.lower()
        
        # Define document type patterns
        document_patterns = {
            'rab': ['rencana anggaran biaya', 'rab', 'bill of quantity', 'boq', 'daftar kuantitas'],
            'contract': ['kontrak', 'perjanjian', 'agreement', 'syarat umum', 'syarat khusus'],
            'specification': ['spesifikasi', 'specification', 'spec', 'mutu', 'kualitas'],
            'drawing': ['gambar kerja', 'drawing', 'denah', 'potongan', 'detail', 'tampak'],
            'report': ['laporan', 'report', 'progress', 'kemajuan', 'evaluasi'],
            'permit': ['izin', 'permit', 'imb', 'siup', 'surat izin']
        }
        
        # Check document type
        max_matches = 0
        detected_type = 'unknown'
        
        for doc_type, keywords in document_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > max_matches:
                max_matches = matches
                detected_type = doc_type
                analysis['keywords_found'] = [kw for kw in keywords if kw in text_lower]
        
        analysis['document_type'] = detected_type
        analysis['confidence_score'] = min(max_matches / 3.0, 1.0)  # Normalize to 0-1
        
        # Extract monetary amounts
        money_patterns = [
            r'(?:Rp\.?\s*)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            r'(\d+(?:\.\d+)?)\s*(?:juta|miliar|ribu)',
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text)
            analysis['currency_amounts'].extend(matches)
        
        # Extract other important numbers
        number_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:m²|m³|m2|m3)',  # Areas and volumes
            r'(\d+(?:\.\d+)?)\s*(?:meter|m)\b',    # Lengths
            r'(\d+(?:\.\d+)?)\s*%',                # Percentages
            r'(\d+(?:\.\d+)?)\s*(?:kg|ton|lt|liter)', # Quantities
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            analysis['numbers_found'].extend(matches)
        
        # Remove duplicates and limit results
        analysis['currency_amounts'] = list(set(analysis['currency_amounts']))[:20]
        analysis['numbers_found'] = list(set(analysis['numbers_found']))[:20]
        
        return analysis
    
    def _extract_tables_from_text(self, text: str) -> List[List[str]]:
        """Basic table extraction from text"""
        import re
        
        tables = []
        lines = text.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_table and current_table:
                    tables.append(current_table)
                    current_table = []
                    in_table = False
                continue
            
            # Simple heuristic: if line has multiple numbers or currency, it might be a table row
            number_count = len(re.findall(r'\d+[.,]?\d*', line))
            
            # Look for common table separators
            has_separators = any(sep in line for sep in ['|', '\t', '  '])
            
            if number_count >= 2 or has_separators:
                in_table = True
                # Split by common separators
                if '|' in line:
                    row = [cell.strip() for cell in line.split('|') if cell.strip()]
                elif '\t' in line:
                    row = [cell.strip() for cell in line.split('\t') if cell.strip()]
                else:
                    # Split by multiple spaces
                    row = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
                
                if row:
                    current_table.append(row)
            else:
                if in_table and current_table:
                    tables.append(current_table)
                    current_table = []
                    in_table = False
        
        # Don't forget the last table
        if current_table:
            tables.append(current_table)
        
        # Filter out tables with less than 2 rows
        tables = [table for table in tables if len(table) >= 2]
        
        return tables
