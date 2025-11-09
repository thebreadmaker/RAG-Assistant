import re
from typing import Optional, Dict

class QueryRouter:
    DEPARTMENTS = {
        "@retail_digital": "retail_digital"
    }
    
    KEYWORDS = {
        "excluded": "lfa",
        "eligible": "lfa",
        "loan": "lfa",
        "qualify": "lfa",
        "arrears": "lfa",
        "dpd": "lfa"
    }
    
    def classify_query(self, query: str) -> Dict:
        tag = self._extract_tag(query)
        customer_id = self._extract_customer_id(query)
        
        query_type = "customer_specific" if customer_id else "general"
        department = self.DEPARTMENTS.get(tag, "retail_digital")
        module = self._match_module(query)
        
        return {
            "department": department,
            "module": module,
            "type": query_type,
            "customer_id": customer_id,
            "original_query": query
        }
    
    def _extract_tag(self, query: str) -> Optional[str]:
        match = re.search(r'@\w+', query)
        return match.group(0) if match else None
    
    def _extract_customer_id(self, query: str) -> Optional[str]:
        match = re.search(r'\b\d{6,}\b', query)
        return match.group(0) if match else None
    
    def _match_module(self, query: str) -> str:
        query_lower = query.lower()
        for keyword, module in self.KEYWORDS.items():
            if keyword in query_lower:
                return module
        return "lfa"

router = QueryRouter()