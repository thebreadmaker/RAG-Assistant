import csv
from typing import Optional, Dict
from pathlib import Path

from fuzzywuzzy import fuzz

class DataLoader:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
    
    def load_customer(self, customer_id: str) -> Optional[Dict]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        
        customer_id_str = str(customer_id).strip()
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('CUS_NO', '').strip() == customer_id_str:
                    return self._map_csv_row(row)
        
        # If exact match not found, try fuzzy matching
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            best_match = None
            best_score = 0
            
            for row in reader:
                csv_id = row.get('CUS_NO', '').strip()
                score = fuzz.ratio(customer_id_str, csv_id)
                
                if score > best_score and score > 85:  # At least 85% match
                    best_score = score
                    best_match = row
            
            if best_match:
                print(f"[INFO] Customer ID fuzzy match: '{customer_id_str}' matched to '{best_match.get('CUS_NO')}' (confidence: {best_score}%)")
                return self._map_csv_row(best_match)
        
        return None

    def _map_csv_row(self, row: Dict) -> Dict:
        """Maps CSV columns to customer model"""
        return {
            "customer_id": row.get('CUS_NO', '').strip(),
            "name": row.get('CUS_NAME_1', '').strip(),
            "account": row.get('ACCOUNT_NUMBER', '').strip(),
            "risk_class": row.get('RISK_CLASS', '').strip(),
            
            # Eligibility check columns (exact match from your CSV)
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
            "Affordability_Check": row.get('Average_Bal_check', '').strip(),  # Using proxy
            
            # Additional data
            "status": row.get('Status', '').strip(),
            "reasons": row.get('reasons', '').strip(),
            "reasons_explanation": row.get('reasons_explanation', '').strip()
        }