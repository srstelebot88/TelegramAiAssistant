import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, Any, Optional, List, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageOCR:
    """OCR processor for technical images and construction drawings"""
    
    def __init__(self):
        self.supported_formats = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif']
        self.max_file_size = 20 * 1024 * 1024  # 20MB for images
        
        # Configure Tesseract
        try:
            # Try to find tesseract executable
            self.tesseract_cmd = self._find_tesseract()
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        except Exception as e:
            logger.warning(f"Tesseract configuration warning: {e}")
    
    def process_image(self, file_path: str, language: str = 'eng+ind') -> Optional[Dict[str, Any]]:
        """Process image with OCR and extract text"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Image file not found: {file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"Image file too large: {file_size} bytes")
                return None
            
            # Check file format
            file_ext = file_path.split('.')[-1].lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Unsupported image format: {file_ext}")
                return None
            
            result = {
                'type': 'image',
                'file_type': file_ext,
                'extracted_text': '',
                'metadata': {
                    'size': file_size,
                    'file_path': file_path,
                    'language': language
                },
                'confidence_scores': [],
                'preprocessing_applied': [],
                'success': True
            }
            
            # Load and analyze image
            image = cv2.imread(file_path)
            if image is None:
                logger.error(f"Failed to load image: {file_path}")
                return None
            
            # Get image properties
            height, width = image.shape[:2]
            result['metadata'].update({
                'width': width,
                'height': height,
                'channels': image.shape[2] if len(image.shape) > 2 else 1,
                'total_pixels': width * height
            })
            
            # Try multiple preprocessing approaches
            ocr_results = []
            
            # 1. Original image
            text, confidence = self._extract_text_with_confidence(image, language)
            if text.strip():
                ocr_results.append({
                    'text': text,
                    'confidence': confidence,
                    'preprocessing': 'original'
                })
            
            # 2. Grayscale conversion
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text, confidence = self._extract_text_with_confidence(gray, language)
            if text.strip():
                ocr_results.append({
                    'text': text,
                    'confidence': confidence,
                    'preprocessing': 'grayscale'
                })
            
            # 3. Noise reduction and enhancement
            enhanced = self._enhance_image_for_ocr(gray)
            text, confidence = self._extract_text_with_confidence(enhanced, language)
            if text.strip():
                ocr_results.append({
                    'text': text,
                    'confidence': confidence,
                    'preprocessing': 'enhanced'
                })
            
            # 4. Binary threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text, confidence = self._extract_text_with_confidence(binary, language)
            if text.strip():
                ocr_results.append({
                    'text': text,
                    'confidence': confidence,
                    'preprocessing': 'binary'
                })
            
            # Select best result
            if ocr_results:
                best_result = max(ocr_results, key=lambda x: x['confidence'])
                result['extracted_text'] = best_result['text']
                result['metadata']['best_preprocessing'] = best_result['preprocessing']
                result['metadata']['confidence'] = best_result['confidence']
                result['confidence_scores'] = [r['confidence'] for r in ocr_results]
                result['preprocessing_applied'] = [r['preprocessing'] for r in ocr_results]
            
            # Analyze extracted text for technical content
            if result['extracted_text']:
                technical_analysis = self._analyze_technical_content(result['extracted_text'])
                result['technical_analysis'] = technical_analysis
            
            # Detect if image contains technical drawings
            drawing_analysis = self._analyze_drawing_content(image)
            result['drawing_analysis'] = drawing_analysis
            
            logger.info(f"OCR processed: {file_path}, confidence: {result['metadata'].get('confidence', 0):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image OCR {file_path}: {e}")
            return {
                'type': 'image',
                'extracted_text': '',
                'metadata': {'error': str(e)},
                'success': False
            }
    
    def extract_tables_from_image(self, file_path: str) -> Optional[List[List[str]]]:
        """Extract table data from image"""
        try:
            result = self.process_image(file_path)
            if not result or not result['success']:
                return None
            
            text = result['extracted_text']
            tables = self._extract_tables_from_ocr_text(text)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from image: {e}")
            return None
    
    def detect_text_regions(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Detect text regions in image"""
        try:
            image = cv2.imread(file_path)
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Use Tesseract to get bounding boxes
            try:
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
                
                text_regions = []
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 30:  # Confidence threshold
                        text_regions.append({
                            'text': data['text'][i],
                            'confidence': int(data['conf'][i]),
                            'bbox': {
                                'x': int(data['left'][i]),
                                'y': int(data['top'][i]),
                                'width': int(data['width'][i]),
                                'height': int(data['height'][i])
                            }
                        })
                
                return text_regions
                
            except Exception as e:
                logger.error(f"Error detecting text regions: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error in detect_text_regions: {e}")
            return None
    
    def _find_tesseract(self) -> Optional[str]:
        """Find Tesseract executable"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            'tesseract'  # In PATH
        ]
        
        for path in possible_paths:
            try:
                import subprocess
                result = subprocess.run([path, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Found Tesseract at: {path}")
                    return path
            except:
                continue
        
        logger.warning("Tesseract not found in common locations")
        return None
    
    def _extract_text_with_confidence(self, image, language: str) -> Tuple[str, float]:
        """Extract text and calculate average confidence"""
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            text_parts = []
            confidences = []
            
            for i in range(len(data['text'])):
                conf = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if conf > 30 and text:  # Filter out low-confidence detections
                    text_parts.append(text)
                    confidences.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.debug(f"Error in OCR extraction: {e}")
            return "", 0.0
    
    def _enhance_image_for_ocr(self, gray_image):
        """Apply image enhancement techniques for better OCR"""
        try:
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray_image)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Morphological operations to clean up
            kernel = np.ones((1,1), np.uint8)
            enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            return enhanced
            
        except Exception as e:
            logger.debug(f"Error in image enhancement: {e}")
            return gray_image
    
    def _analyze_technical_content(self, text: str) -> Dict[str, Any]:
        """Analyze text for technical construction content"""
        import re
        
        analysis = {
            'has_dimensions': False,
            'has_materials': False,
            'has_specifications': False,
            'has_codes': False,
            'dimensions_found': [],
            'materials_found': [],
            'codes_found': [],
            'technical_score': 0.0
        }
        
        text_lower = text.lower()
        
        # Look for dimensions
        dimension_patterns = [
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',  # 10x20
            r'(\d+(?:\.\d+)?)\s*m[m²³]?',  # 10mm, 5m²
            r'(\d+(?:\.\d+)?)\s*(?:cm|mm|meter)',  # 10cm, 5mm
            r'(?:diameter|dia\.?|ø)\s*(\d+(?:\.\d+)?)',  # diameter 10
        ]
        
        for pattern in dimension_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                analysis['has_dimensions'] = True
                analysis['dimensions_found'].extend([str(m) for m in matches[:10]])
        
        # Look for materials
        material_keywords = [
            'beton', 'concrete', 'steel', 'baja', 'besi', 'kayu', 'wood',
            'semen', 'cement', 'agregat', 'aggregate', 'pasir', 'sand',
            'keramik', 'ceramic', 'granit', 'granite'
        ]
        
        for material in material_keywords:
            if material in text_lower:
                analysis['has_materials'] = True
                analysis['materials_found'].append(material)
        
        # Look for specifications and codes
        spec_patterns = [
            r'(?:mutu|grade|class)\s*[K-]?\s*(\d+)',  # Mutu K-300
            r'(?:SNI|ASTM|BS|DIN)\s*[\d-]+',  # SNI 03-2847-2013
            r'(?:fc\'?|fy)\s*=?\s*(\d+)\s*MPa',  # fc' = 25 MPa
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                analysis['has_specifications'] = True
                analysis['codes_found'].extend([str(m) for m in matches[:5]])
        
        # Calculate technical score
        score = 0
        if analysis['has_dimensions']: score += 0.3
        if analysis['has_materials']: score += 0.3
        if analysis['has_specifications']: score += 0.4
        
        analysis['technical_score'] = score
        
        return analysis
    
    def _analyze_drawing_content(self, image) -> Dict[str, Any]:
        """Analyze if image contains technical drawings"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            analysis = {
                'has_lines': False,
                'has_geometric_shapes': False,
                'line_density': 0.0,
                'drawing_score': 0.0
            }
            
            # Detect lines using HoughLines
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                analysis['has_lines'] = True
                analysis['line_density'] = len(lines) / (image.shape[0] * image.shape[1] / 1000000)
            
            # Detect contours (geometric shapes)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            geometric_shapes = 0
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Count shapes with 3-8 vertices (triangles to octagons)
                if 3 <= len(approx) <= 8 and cv2.contourArea(contour) > 100:
                    geometric_shapes += 1
            
            if geometric_shapes > 5:
                analysis['has_geometric_shapes'] = True
            
            # Calculate drawing score
            score = 0
            if analysis['has_lines']: score += 0.4
            if analysis['has_geometric_shapes']: score += 0.3
            if analysis['line_density'] > 0.1: score += 0.3
            
            analysis['drawing_score'] = min(score, 1.0)
            
            return analysis
            
        except Exception as e:
            logger.debug(f"Error analyzing drawing content: {e}")
            return {'drawing_score': 0.0}
    
    def _extract_tables_from_ocr_text(self, text: str) -> List[List[str]]:
        """Extract table-like structures from OCR text"""
        import re
        
        lines = text.split('\n')
        tables = []
        current_table = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_table:
                    tables.append(current_table)
                    current_table = []
                continue
            
            # Look for table-like patterns
            # Multiple numbers or values separated by spaces/tabs
            parts = re.split(r'\s{2,}|\t', line)
            if len(parts) >= 2:
                # Clean up parts
                cleaned_parts = [part.strip() for part in parts if part.strip()]
                if len(cleaned_parts) >= 2:
                    current_table.append(cleaned_parts)
            else:
                # Check for delimiter-separated values
                for delimiter in ['|', ';', ',']:
                    if delimiter in line:
                        parts = [part.strip() for part in line.split(delimiter) if part.strip()]
                        if len(parts) >= 2:
                            current_table.append(parts)
                            break
        
        # Don't forget the last table
        if current_table:
            tables.append(current_table)
        
        # Filter out tables with less than 2 rows
        return [table for table in tables if len(table) >= 2]
