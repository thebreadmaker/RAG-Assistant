import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from departments.retail_digital.modules.lfa.data_loader import DataLoader
from core.cache import cache
from core.config import get_settings

settings = get_settings()

class LFAProcessor:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.rules = self._load_rules()
        self.data_loader = DataLoader(self.base_path / "data" / "reasons.csv")
    
    def _load_rules(self) -> Dict:
        rules_path = self.base_path / "rules.yaml"
        with open(rules_path, 'r') as f:
            return yaml.safe_load(f)
    
    def check_eligibility(self, customer_id: str) -> Dict:
        # Try cache first
        cache_key = f"eligibility:{customer_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Load customer data
        customer = self._get_customer(customer_id)
        if not customer:
            return {"status": "not_found", "message": "Customer not found"}
        
        # Run eligibility checks
        result = self._run_checks(customer)
        
        # Cache result
        cache.set(cache_key, result, settings.query_cache_ttl)
        
        return result
    
    def _get_customer(self, customer_id: str) -> Dict:
        cache_key = f"customer:{customer_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        customer = self.data_loader.load_customer(customer_id)
        if customer:
            cache.set(cache_key, customer, settings.customer_cache_ttl)
        
        return customer
    
    def _run_checks(self, customer: Dict) -> Dict:
        checks = {}
        failed_checks = []
        
        lfa_config = self.rules['lfa_loan']
        
        for check in lfa_config['eligibility_checks']:
            check_name = check['name']
            csv_column = check['csv_column']
            required_value = check['required_value']
            
            actual_value = customer.get(csv_column, '').strip()
            
            if actual_value == required_value:
                checks[check_name] = "Include"
            else:
                checks[check_name] = "Exclude"
                failed_checks.append({
                    "check": check_name,
                    "reason": check['exclusion_reason'],
                    "expected": required_value,
                    "actual": actual_value,
                    "description": check['description']
                })
        
        overall_status = "Include" if len(failed_checks) == 0 else "Exclude"
        
        # Calculate next review date
        next_review = self._calculate_next_review(failed_checks, lfa_config)
        
        return {
            "customer_id": customer['customer_id'],
            "customer_name": customer['name'],
            "overall_status": overall_status,
            "checks": checks,
            "failed_checks": failed_checks,
            "next_review_date": next_review,
            "actions": self._generate_actions(failed_checks)
        }
    
    def _calculate_next_review(self, failed_checks: List[Dict], config: Dict) -> str:
        # If DPD check failed, apply cooling period
        dpd_failed = any(c['check'] == 'DPD_Arrears_Check_DS' for c in failed_checks)
        
        if dpd_failed:
            days = config['dpd_cooling_period_days']
        else:
            days = 30  # Standard review cycle
        
        next_date = datetime.now() + timedelta(days=days)
        return next_date.strftime("%Y-%m-%d")
    
    def _generate_actions(self, failed_checks: List[Dict]) -> List[str]:
        actions = []
        
        for check in failed_checks:
            if check['check'] == 'DPD_Arrears_Check_DS':
                actions.append("Clear all overdue loan amounts")
                actions.append("Wait 60 days after clearance (cooling period)")
            elif check['check'] == 'customer_vintage_Check':
                actions.append("Continue banking for at least 6 months")
            elif check['check'] == 'Turnover_Check':
                actions.append("Increase account turnover consistency")
            elif check['check'] == 'Active_Inactive_Check':
                actions.append("Ensure account and mobile banking are active")
            else:
                actions.append(f"Resolve: {check['description']}")
        
        if not actions:
            actions.append("Customer is eligible - no action needed")
        
        return list(set(actions))  # Remove duplicates

processor = LFAProcessor()