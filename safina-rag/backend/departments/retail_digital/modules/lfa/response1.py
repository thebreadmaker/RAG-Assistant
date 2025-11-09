import requests
from typing import Dict
from core.config import get_settings

settings = get_settings()

class ResponseGenerator:
    def __init__(self):
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.model = settings.ollama_model
    
    def generate(self, eligibility_result: Dict, query: str) -> str:
        if eligibility_result.get("status") == "not_found":
            return "I couldn't find that customer in our records. Please verify the customer ID."
        
        prompt = self._build_prompt(eligibility_result, query)
        
        try:
            response = self._call_llm(prompt)
            return self._clean_response(response)
        except Exception as e:
            return self._fallback_response(eligibility_result)
    
    def _build_prompt(self, result: Dict, query: str) -> str:
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        failed_checks = result.get('failed_checks', [])
        next_review = result.get('next_review_date', 'Unknown')
        actions = result.get('actions', [])
        
        if status == "Include":
            return f"""Customer {customer_name} (ID: {customer_id}) is ELIGIBLE for an LFA loan.

All eligibility checks passed. They can proceed with their loan application.

Respond in a friendly, professional tone."""
        
        # Build exclusion details
        exclusion_details = "\n".join([
            f"- {check['check']}: {check['description']}" 
            for check in failed_checks[:3]  # Limit to top 3
        ])
        
        action_steps = "\n".join([f"• {action}" for action in actions[:3]])
        
        return f"""You are a helpful banking assistant. Answer this query: "{query}"

Customer: {customer_name} (ID: {customer_id})
Status: NOT ELIGIBLE (Excluded)

Failed Checks:
{exclusion_details}

Required Actions:
{action_steps}

Next Review Date: {next_review}

Provide a clear, empathetic explanation in 2-3 short paragraphs:
1. What's wrong (in plain language)
2. What they need to do
3. When they can reapply

Keep it conversational and helpful. Don't use technical jargon."""
    
    def _call_llm(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 300
            }
        }
        
        response = requests.post(self.ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def _clean_response(self, response: str) -> str:
        # Remove any system artifacts
        response = response.strip()
        # Remove common LLM artifacts
        response = response.replace("Assistant:", "").strip()
        return response
    
    def _fallback_response(self, result: Dict) -> str:
        """Simple template-based response if LLM fails"""
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        
        if status == "Include":
            return f"{customer_name} (ID: {customer_id}) is eligible for an LFA loan. All checks passed."
        
        failed = result.get('failed_checks', [])
        if not failed:
            return f"{customer_name} (ID: {customer_id}) status: {status}"
        
        reasons = ", ".join([c['check'] for c in failed[:2]])
        next_review = result.get('next_review_date', 'Unknown')
        
        return f"""{customer_name} (ID: {customer_id}) is currently not eligible.

Issues: {reasons}

Next review date: {next_review}

Please contact customer support for detailed guidance."""

generator = ResponseGenerator()