from typing import List, Dict, Any, Optional
import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

class KnowledgeRetriever:
    """Retrieve information from construction and tax knowledge base"""
    
    def __init__(self):
        self.kb_data = self._load_knowledge_base()
    
    def search_knowledge(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        try:
            results = []
            query_lower = query.lower()
            
            for item in self.kb_data:
                # Check category filter
                if category and item.get('category') != category:
                    continue
                
                # Simple keyword matching
                title_match = any(word in item.get('title', '').lower() for word in query_lower.split())
                content_match = any(word in item.get('content', '').lower() for word in query_lower.split())
                keywords_match = any(word in ' '.join(item.get('keywords', [])).lower() for word in query_lower.split())
                
                if title_match or content_match or keywords_match:
                    # Calculate relevance score
                    score = 0
                    if title_match: score += 3
                    if content_match: score += 2
                    if keywords_match: score += 1
                    
                    item_copy = item.copy()
                    item_copy['relevance_score'] = score
                    results.append(item_copy)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return results[:10]  # Return top 10 results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def get_categories(self) -> List[str]:
        """Get available knowledge categories"""
        categories = set()
        for item in self.kb_data:
            if 'category' in item:
                categories.add(item['category'])
        return list(categories)
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load knowledge base data"""
        # Default construction and tax knowledge
        default_kb = [
            {
                "id": "sni_beton_1",
                "title": "SNI 2847:2019 - Persyaratan Beton Struktural",
                "category": "standards",
                "content": "Standar Nasional Indonesia untuk persyaratan beton struktural mencakup desain, material, konstruksi, dan evaluasi kekuatan beton. Mutu beton minimum K-225 untuk struktur bangunan bertingkat.",
                "keywords": ["sni", "beton", "struktural", "mutu", "k-225"],
                "reference": "BSN 2019"
            },
            {
                "id": "tax_construction_1",
                "title": "PPh Final Pasal 4(2) - Jasa Konstruksi",
                "category": "tax",
                "content": "Pajak Penghasilan Final untuk jasa konstruksi dikenakan tarif 2% dari nilai bruto kontrak. Berlaku untuk kontraktor dengan kualifikasi usaha kecil, menengah, dan besar.",
                "keywords": ["pph", "final", "konstruksi", "2%", "kontraktor"],
                "reference": "PP No. 23 Tahun 2018"
            },
            {
                "id": "volume_calculation_1",
                "title": "Perhitungan Volume Beton",
                "category": "calculation",
                "content": "Volume beton dihitung berdasarkan dimensi struktur dengan tambahan waste factor 5-10%. Untuk kolom: V = L x W x H, untuk balok: V = W x H x L, untuk plat: V = L x W x t.",
                "keywords": ["volume", "beton", "kolom", "balok", "plat", "waste"],
                "reference": "Standar Konstruksi"
            },
            {
                "id": "material_price_1",
                "title": "Harga Satuan Material Konstruksi 2024",
                "category": "pricing",
                "content": "Referensi harga material: Beton ready mix K-300 Rp 800.000/m³, Besi beton Rp 14.000/kg, Semen Portland Rp 65.000/sak, Pasir beton Rp 350.000/m³, Kerikil Rp 400.000/m³.",
                "keywords": ["harga", "material", "beton", "besi", "semen", "pasir"],
                "reference": "Survey Pasar 2024"
            },
            {
                "id": "quality_control_1",
                "title": "Kontrol Kualitas Beton",
                "category": "quality",
                "content": "Pengujian kuat tekan beton dilakukan pada umur 7, 14, dan 28 hari. Minimal 1 sampel per 100m³ atau per hari pengecoran. Standar kuat tekan minimum 85% dari fc' rencana.",
                "keywords": ["kualitas", "beton", "test", "tekan", "sampel"],
                "reference": "SNI 03-2847"
            }
        ]
        
        # Try to load from file if exists
        kb_file = "knowledge_base/internal_kb.json"
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    loaded_kb = json.load(f)
                    logger.info(f"Loaded {len(loaded_kb)} items from knowledge base file")
                    return loaded_kb
            except Exception as e:
                logger.warning(f"Failed to load knowledge base file: {e}")
        
        return default_kb