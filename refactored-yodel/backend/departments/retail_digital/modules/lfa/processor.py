import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from departments.retail_digital.modules.lfa.data_loader import DataLoader
from core.cache import cache
from core.config import get_settings
from core.logger import logger

settings = get_settings()

class LFAProcessor:
    def __init__(self):
        logger.info(f"📋 Initializing LFAProcessor")
        self.base_path = Path(__file__).parent
        self.rules = self._load_rules()
        self.data_loader = DataLoader(self.base_path / "data" / "reasons.csv")
        logger.debug(f"   Rules loaded: {len(self.rules)} sections")
        logger.info(f"✅ LFAProcessor initialized")
    
    def _load_rules(self) -> Dict:
        rules_path = self.base_path / "rules.yaml"
        logger.debug(f"   Loading rules from: {rules_path}")
        with open(rules_path, 'r') as f:
            return yaml.safe_load(f)
    
    def check_eligibility(self, customer_id: str) -> Dict:
        """Check LFA eligibility for a customer"""
        logger.info(f"👤 Eligibility check started for customer: {customer_id}")
        
        # Try cache first
        cache_key = f"eligibility:{customer_id}"
        logger.debug(f"   Checking cache: {cache_key}")
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"   ✅ Cache HIT - Returning cached eligibility")
            return cached
        
        logger.debug(f"   Cache MISS - Loading customer data...")
        
        # Load customer data
        customer = self._get_customer(customer_id)
        if not customer:
            logger.warning(f"   ⚠️ Customer not found: {customer_id}")
            return {"status": "not_found", "message": "Customer not found"}
        
        logger.info(f"   ✅ Customer loaded: {customer.get('name', 'Unknown')}")
        
        # Run eligibility checks
        logger.debug(f"   Running eligibility checks...")
        result = self._run_checks(customer)
        
        logger.info(f"   Overall status: {result.get('overall_status')}")
        if result.get('failed_checks'):
            logger.info(f"   Failed checks: {len(result['failed_checks'])}")
            for check in result['failed_checks'][:3]:
                logger.debug(f"      - {check['check']}: {check['reason']}")
        
        # Cache result
        logger.debug(f"   Caching eligibility result (TTL: {settings.query_cache_ttl}s)")
        cache.set(cache_key, result, settings.query_cache_ttl)
        
        logger.info(f"✅ Eligibility check complete")
        return result
    
    def _get_customer(self, customer_id: str) -> Dict:
        """Load customer data with caching"""
        cache_key = f"customer:{customer_id}"
        logger.debug(f"   Customer cache key: {cache_key}")
        
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"   ✅ Customer cache HIT")
            return cached
        
        logger.debug(f"   Loading customer from data loader...")
        customer = self.data_loader.load_customer(customer_id)
        
        if customer:
            logger.debug(f"   ✅ Customer loaded, caching (TTL: {settings.customer_cache_ttl}s)")
            cache.set(cache_key, customer, settings.customer_cache_ttl)
            logger.debug(f"      Fields: {list(customer.keys())}")
        else:
            logger.debug(f"   ❌ Customer not found in data loader")
        
        return customer
    
    def _run_checks(self, customer: Dict) -> Dict:
        """Run all eligibility checks"""
        logger.debug(f"   Running eligibility checks for {customer.get('customer_id')}")
        
        checks = {}
        failed_checks = []
        
        lfa_config = self.rules['lfa_loan']
        check_count = len(lfa_config['eligibility_checks'])
        logger.debug(f"   Total checks to run: {check_count}")
        
        for check_idx, check in enumerate(lfa_config['eligibility_checks'], 1):
            check_name = check['name']
            csv_column = check['csv_column']
            required_value = check['required_value']
            
            actual_value = customer.get(csv_column, '').strip()
            
            logger.debug(f"   Check {check_idx}/{check_count}: {check_name}")
            logger.debug(f"      Column: {csv_column}, Expected: {required_value}, Actual: {actual_value}")
            
            if actual_value == required_value:
                checks[check_name] = "Include"
                logger.debug(f"      ✅ PASS - Included")
            else:
                checks[check_name] = "Exclude"
                failed_checks.append({
                    "check": check_name,
                    "reason": check['exclusion_reason'],
                    "expected": required_value,
                    "actual": actual_value,
                    "description": check['description']
                })
                logger.debug(f"      ❌ FAIL - Excluded: {check['exclusion_reason']}")
        
        overall_status = "Include" if len(failed_checks) == 0 else "Exclude"
        logger.info(f"   Checks complete: {len(checks) - len(failed_checks)}/{check_count} passed")
        
        # Calculate next review date
        next_review = self._calculate_next_review(failed_checks, lfa_config)
        logger.debug(f"   Next review date: {next_review}")
        
        # Generate actions
        actions = self._generate_actions(failed_checks)
        logger.debug(f"   Generated {len(actions)} action(s)")
        
        return {
            "customer_id": customer['customer_id'],
            "customer_name": customer['name'],
            "overall_status": overall_status,
            "checks": checks,
            "failed_checks": failed_checks,
            "next_review_date": next_review,
            "actions": actions
        }
    
    def _calculate_next_review(self, failed_checks: List[Dict], config: Dict) -> str:
        """Calculate next review date based on failed checks"""
        # If DPD check failed, apply cooling period
        dpd_failed = any(c['check'] == 'DPD_Arrears_Check_DS' for c in failed_checks)
        
        if dpd_failed:
            days = config['dpd_cooling_period_days']
            logger.debug(f"   DPD check failed - applying cooling period: {days} days")
        else:
            days = 30  # Standard review cycle
            logger.debug(f"   Standard review cycle: {days} days")
        
        next_date = datetime.now() + timedelta(days=days)
        return next_date.strftime("%Y-%m-%d")
    
    def _generate_actions(self, failed_checks: List[Dict]) -> List[str]:
        """Generate recommended actions based on failed checks"""
        logger.debug(f"   Generating {len(failed_checks)} action(s) for failed checks")
        
        actions = []
        
        for check in failed_checks:
            check_name = check['check']
            if check_name == 'DPD_Arrears_Check_DS':
                actions.append("Clear all overdue loan amounts")
                actions.append("Wait 60 days after clearance (cooling period)")
                logger.debug(f"      Added DPD actions")
            elif check_name == 'customer_vintage_Check':
                actions.append("Continue banking for at least 6 months")
                logger.debug(f"      Added vintage actions")
            elif check_name == 'Turnover_Check':
                actions.append("Increase account turnover consistency")
                logger.debug(f"      Added turnover actions")
            elif check_name == 'Active_Inactive_Check':
                actions.append("Ensure account and mobile banking are active")
                logger.debug(f"      Added activity actions")
            else:
                actions.append(f"Resolve: {check['description']}")
                logger.debug(f"      Added generic action for {check_name}")
        
        if not actions:
            actions.append("Customer is eligible - no action needed")
            logger.debug(f"   No failed checks - customer is eligible")
        
        return list(set(actions))  # Remove duplicates

processor = LFAProcessor()