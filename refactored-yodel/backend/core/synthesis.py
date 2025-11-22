"""
Synthesis Engine - Combines structured data with document chunks
"""
from typing import Dict, List
from core.structured_data import get_structured_loader
from core.logger import logger

class SynthesisEngine:
    def __init__(self, department: str):
        self.department = department
        self.structured_loader = get_structured_loader(department)
    
    def synthesize(
        self, 
        query: str, 
        customer_ids: List[str], 
        topics: List[str],
        policy_chunks: List[Dict]
    ) -> Dict:
        """
        Combine customer data with relevant policies
        Returns structured context for LLM
        """
        logger.info(f"🔗 Synthesis started - Customers: {customer_ids}, Topics: {topics}")
        
        # Step 1: Retrieve structured data
        customer_data = []
        for cust_id in customer_ids:
            data = self.structured_loader.lookup_customer(cust_id)
            if data:
                customer_data.append(data)
                logger.debug(f"Retrieved data for customer {cust_id}")
        
        if not customer_data:
            logger.warning("No customer data found")
            return {
                "has_customer_data": False,
                "has_policy_data": len(policy_chunks) > 0,
                "context": self._build_fallback_context(policy_chunks)
            }
        
        # Step 2: Build synthesis context
        context = self._build_synthesis_context(
            customer_data=customer_data,
            policy_chunks=policy_chunks,
            topics=topics
        )
        
        logger.info(f"✅ Synthesis complete - Context length: {len(context)} chars")
        
        return {
            "has_customer_data": True,
            "has_policy_data": len(policy_chunks) > 0,
            "context": context,
            "customer_count": len(customer_data),
            "policy_count": len(policy_chunks)
        }
    
    def _build_synthesis_context(
        self, 
        customer_data: List[Dict], 
        policy_chunks: List[Dict],
        topics: List[str]
    ) -> str:
        """Build structured context for LLM"""
        
        context_parts = ["=== CUSTOMER DATA ===\n"]
        
        # Add customer information
        for cust in customer_data:
            context_parts.append(f"Customer ID: {cust.get('CUS_NO')}")
            context_parts.append(f"Name: {cust.get('CUS_NAME_1')}")
            context_parts.append(f"Days in Arrears: {cust.get('DPD_Arrears_Check_DS')}")
            context_parts.append(f"Status: {cust.get('Status')}")
            context_parts.append(f"Reasons: {cust.get('reasons_explanation', 'N/A')}")
            context_parts.append("")
        
        context_parts.append("\n=== RELEVANT POLICIES ===\n")
        
        # Add policy chunks
        for i, chunk in enumerate(policy_chunks[:3], 1):
            source = chunk["metadata"].get("source", "Unknown")
            text = chunk["text"][:400]  # Limit length
            context_parts.append(f"[Policy {i}: {source}]")
            context_parts.append(text)
            context_parts.append("")
        
        context_parts.append("\n=== CROSS-REFERENCE ===")
        
        # Add synthesis instructions
        if customer_data and topics:
            context_parts.append(f"Connect customer {customer_data[0].get('CUS_NO')}'s situation with {', '.join(topics)} policy")
        
        return "\n".join(context_parts)
    
    def _build_fallback_context(self, policy_chunks: List[Dict]) -> str:
        """Fallback context when no customer data"""
        context_parts = ["=== RELEVANT POLICIES ===\n"]
        
        for i, chunk in enumerate(policy_chunks[:3], 1):
            source = chunk["metadata"].get("source", "Unknown")
            text = chunk["text"][:400]
            context_parts.append(f"[Policy {i}: {source}]")
            context_parts.append(text)
            context_parts.append("")
        
        return "\n".join(context_parts)

# Singleton
_synthesis_engine = None

def get_synthesis_engine(department: str = "retail_digital"):
    global _synthesis_engine
    if _synthesis_engine is None:
        _synthesis_engine = SynthesisEngine(department)
    return _synthesis_engine