from typing import Dict, Any, Optional
import math
from utils.logger import get_logger

logger = get_logger(__name__)

class ConstructionCalculator:
    """Calculator for construction volumes, costs, and materials"""
    
    def __init__(self):
        # Default construction rates and prices (Indonesia market)
        self.default_rates = {
            'labor_percentage': 0.30,
            'material_percentage': 0.60,
            'overhead_percentage': 0.10,
            'markup_percentage': 0.15
        }
        
        # Material unit prices (IDR per unit)
        self.material_prices = {
            'beton_k300': 800000,  # per m³
            'besi_beton_10mm': 14000,  # per kg
            'semen': 65000,  # per sak 40kg
            'pasir': 350000,  # per m³
            'kerikil': 400000,  # per m³
            'bata_merah': 800,  # per biji
            'genteng': 5000,  # per biji
            'cat': 150000,  # per galon
            'kayu_meranti': 8000000,  # per m³
        }
    
    def calculate_volume(self, calc_type: str, dimensions: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Calculate construction volumes"""
        try:
            if calc_type == 'rectangular':
                return self._calc_rectangular_volume(dimensions)
            elif calc_type == 'cylindrical':
                return self._calc_cylindrical_volume(dimensions)
            elif calc_type == 'foundation':
                return self._calc_foundation_volume(dimensions)
            elif calc_type == 'column':
                return self._calc_column_volume(dimensions)
            elif calc_type == 'beam':
                return self._calc_beam_volume(dimensions)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error calculating volume: {e}")
            return None
    
    def calculate_cost_estimate(self, project_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate cost estimate for construction project"""
        try:
            volume = project_data.get('volume', 0)
            project_type = project_data.get('type', 'general')
            
            # Base cost per m³ based on project type
            base_costs = {
                'residential': 2500000,  # IDR per m³
                'commercial': 3500000,
                'industrial': 4000000,
                'infrastructure': 5000000,
                'general': 3000000
            }
            
            base_cost_per_m3 = base_costs.get(project_type, base_costs['general'])
            total_base_cost = volume * base_cost_per_m3
            
            # Calculate breakdown
            material_cost = total_base_cost * self.default_rates['material_percentage']
            labor_cost = total_base_cost * self.default_rates['labor_percentage']
            overhead_cost = total_base_cost * self.default_rates['overhead_percentage']
            
            subtotal = material_cost + labor_cost + overhead_cost
            markup = subtotal * self.default_rates['markup_percentage']
            total_cost = subtotal + markup
            
            return {
                'volume': volume,
                'unit': 'm³',
                'base_cost_per_m3': base_cost_per_m3,
                'breakdown': {
                    'Material': material_cost,
                    'Tenaga Kerja': labor_cost,
                    'Overhead': overhead_cost,
                    'Markup': markup
                },
                'subtotal': subtotal,
                'total_cost': total_cost,
                'project_type': project_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating cost estimate: {e}")
            return None
    
    def calculate_material_needs(self, volume: float, structure_type: str) -> Optional[Dict[str, Any]]:
        """Calculate material requirements"""
        try:
            materials = {}
            
            if structure_type == 'concrete_slab':
                # Concrete slab material calculation
                materials = {
                    'beton_ready_mix': {
                        'quantity': volume * 1.05,  # 5% waste factor
                        'unit': 'm³',
                        'price': self.material_prices['beton_k300'],
                        'total': volume * 1.05 * self.material_prices['beton_k300']
                    },
                    'besi_beton': {
                        'quantity': volume * 120,  # kg per m³
                        'unit': 'kg',
                        'price': self.material_prices['besi_beton_10mm'],
                        'total': volume * 120 * self.material_prices['besi_beton_10mm']
                    }
                }
            
            elif structure_type == 'brick_wall':
                # Brick wall material calculation
                area = volume  # Assuming volume is wall area for this case
                materials = {
                    'bata_merah': {
                        'quantity': area * 70,  # bricks per m²
                        'unit': 'biji',
                        'price': self.material_prices['bata_merah'],
                        'total': area * 70 * self.material_prices['bata_merah']
                    },
                    'semen': {
                        'quantity': area * 2,  # sacks per m²
                        'unit': 'sak',
                        'price': self.material_prices['semen'],
                        'total': area * 2 * self.material_prices['semen']
                    },
                    'pasir': {
                        'quantity': area * 0.04,  # m³ per m²
                        'unit': 'm³',
                        'price': self.material_prices['pasir'],
                        'total': area * 0.04 * self.material_prices['pasir']
                    }
                }
            
            # Calculate total cost
            total_cost = sum(mat['total'] for mat in materials.values())
            
            return {
                'structure_type': structure_type,
                'materials': materials,
                'total_cost': total_cost
            }
            
        except Exception as e:
            logger.error(f"Error calculating material needs: {e}")
            return None
    
    def _calc_rectangular_volume(self, dims: Dict[str, float]) -> Dict[str, Any]:
        """Calculate rectangular volume"""
        length = dims.get('length', 0)
        width = dims.get('width', 0)
        height = dims.get('height', 0)
        
        volume = length * width * height
        
        return {
            'volume': volume,
            'unit': 'm³',
            'breakdown': {
                'Panjang': f"{length} m",
                'Lebar': f"{width} m",
                'Tinggi': f"{height} m",
                'Formula': "P × L × T"
            }
        }
    
    def _calc_cylindrical_volume(self, dims: Dict[str, float]) -> Dict[str, Any]:
        """Calculate cylindrical volume"""
        radius = dims.get('radius', 0)
        height = dims.get('height', 0)
        
        volume = math.pi * radius * radius * height
        
        return {
            'volume': volume,
            'unit': 'm³',
            'breakdown': {
                'Radius': f"{radius} m",
                'Tinggi': f"{height} m",
                'Formula': "π × r² × h"
            }
        }
    
    def _calc_foundation_volume(self, dims: Dict[str, float]) -> Dict[str, Any]:
        """Calculate foundation volume"""
        length = dims.get('length', 0)
        width = dims.get('width', 0)
        depth = dims.get('depth', 0)
        
        volume = length * width * depth
        
        return {
            'volume': volume,
            'unit': 'm³',
            'breakdown': {
                'Panjang': f"{length} m",
                'Lebar': f"{width} m",
                'Kedalaman': f"{depth} m",
                'Formula': "P × L × D"
            }
        }
    
    def _calc_column_volume(self, dims: Dict[str, float]) -> Dict[str, Any]:
        """Calculate column volume"""
        width = dims.get('width', 0)
        depth = dims.get('depth', 0)
        height = dims.get('height', 0)
        count = dims.get('count', 1)
        
        single_volume = width * depth * height
        total_volume = single_volume * count
        
        return {
            'volume': total_volume,
            'unit': 'm³',
            'breakdown': {
                'Lebar': f"{width} m",
                'Tebal': f"{depth} m",
                'Tinggi': f"{height} m",
                'Jumlah': f"{count} buah",
                'Volume per kolom': f"{single_volume:.3f} m³"
            }
        }
    
    def _calc_beam_volume(self, dims: Dict[str, float]) -> Dict[str, Any]:
        """Calculate beam volume"""
        width = dims.get('width', 0)
        height = dims.get('height', 0)
        length = dims.get('length', 0)
        count = dims.get('count', 1)
        
        single_volume = width * height * length
        total_volume = single_volume * count
        
        return {
            'volume': total_volume,
            'unit': 'm³',
            'breakdown': {
                'Lebar': f"{width} m",
                'Tinggi': f"{height} m",
                'Panjang': f"{length} m",
                'Jumlah': f"{count} buah",
                'Volume per balok': f"{single_volume:.3f} m³"
            }
        }