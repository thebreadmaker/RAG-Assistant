"""
Structured Data Layer - Fast lookup for CSV data
"""
import csv
from pathlib import Path
from typing import Optional, Dict, List
from core.logger import logger

class StructuredDataLoader:
    def __init__(self, department: str):
        self.department = department
        self.data_cache = {}
        self._load_data()
    
    def _load_data(self):
        """Load CSV data into memory for fast lookup"""
        base_path = Path(__file__).parent.parent / "departments" / self.department / "modules" / "lfa" / "data"
        
        csv_file = base_path / "reasons.csv"
        if not csv_file.exists():
            logger.warning(f"No structured data found at {csv_file}")
            return
        
        logger.info(f"Loading structured data from {csv_file}")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                customer_id = row.get('CUS_NO', '').strip()
                if customer_id:
                    self.data_cache[customer_id] = row
        
        logger.info(f"Loaded {len(self.data_cache)} customer records")
    
    def lookup_customer(self, customer_id: str) -> Optional[Dict]:
        """Fast O(1) lookup by customer ID"""
        return self.data_cache.get(str(customer_id).strip())
    
    def search_by_criteria(self, criteria: Dict) -> List[Dict]:
        """Search customers by criteria (e.g., arrears status)"""
        results = []
        for cust_id, data in self.data_cache.items():
            match = True
            for key, value in criteria.items():
                if data.get(key, '').strip() != str(value).strip():
                    match = False
                    break
            if match:
                results.append(data)
        return results
    
    def get_arrears_data(self, customer_id: str) -> Optional[Dict]:
        """Get arrears-specific data for a customer"""
        customer = self.lookup_customer(customer_id)
        if not customer:
            return None
        
        return {
            "customer_id": customer.get('CUS_NO'),
            "name": customer.get('CUS_NAME_1'),
            "days_in_arrears": customer.get('DPD_Arrears_Check_DS'),
            "status": customer.get('Status'),
            "reasons": customer.get('reasons'),
            "reasons_explanation": customer.get('reasons_explanation')
        }

# Singleton instance
_loader = None

def get_structured_loader(department: str = "retail_digital"):
    global _loader
    if _loader is None:
        _loader = StructuredDataLoader(department)
    return _loader