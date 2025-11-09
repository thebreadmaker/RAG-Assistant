import csv
from typing import Optional, Dict
from pathlib import Path

class DataLoader:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
    
    def load_customer(self, customer_id: str) -> Optional[Dict]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('CUS_NO', '').strip() == str(customer_id).strip():
                    return self._map_csv_row(row)
        
        return None
    
    def _map_csv_row(self, row: Dict) -> Dict:
        """Maps CSV columns to customer model"""
        return {
            "customer_id": row.get('CUS_NO', '').strip(),
            "name": row.get('CUS_NAME_1', '').strip(),
            "account": row.get('ACCOUNT_NUMBER', '').strip(),
            
            # Eligibility check columns (mapped from your CSV)
            "Elma_check": row.get('Elma_check', '').strip(),
            "Joint_Check": row.get('Joint_Check', '').strip(),
            "Mandates_Check": row.get('Mandates_Check', '').strip(),
            "Classification_Check": row.get('Classification_Check', '').strip(),
            "Risk_Class_Check_DS": row.get('Risk_Class_Check_DS', '').strip(),
            "customer_vintage_Check": row.get('customer_vintage_Check', '').strip(),
            "DPD_Arrears_Check_DS": row.get('DPD_Arrears_Check_DS', '').strip(),
            "recency_check": row.get('recency_check', '').strip(),
            "Turnover_Check": row.get('Turnover_Check', '').strip(),
            "Active_Inactive_Check": row.get('Active_Inactive_Check', '').strip(),
            "Linked_Base_Check": row.get('Linked_Base_Check', '').strip(),
            "Scheme_Check_DS": row.get('Scheme_Check_DS', '').strip(),
            "Staff_Check_DS": row.get('Staff_Check_DS', '').strip(),
            "USAID_Check_DS": row.get('USAID_Check_DS', '').strip(),
            "Affordability_Check": row.get('Affordability_Check', '').strip(),
            
            # Additional data
            "dpd_days": row.get('DPD_DAYS', '0').strip(),
            "reasons": row.get('reasons', '').strip()
        }