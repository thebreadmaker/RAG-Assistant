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
            print(f"LLM generation failed: {e}")
            return self._fallback_response(eligibility_result)
    
    def _build_prompt(self, result: Dict, query: str) -> str:
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        failed_checks = result.get('failed_checks', [])
        next_review = result.get('next_review_date', 'Unknown')
        actions = result.get('actions', [])
        
        if status == "Include":
            return f"""Write a short response. Do not create a conversation.

FACTS:
- Customer: {customer_name}
- ID: {customer_id}
- Status: ELIGIBLE
- All checks passed

Write only this: "Good news! {customer_name} (ID: {customer_id}) is eligible for an LFA loan. All eligibility checks have passed and they can proceed with their application."

Do not add anything else."""
        
        # Build simple, clear issue list
        issues = []
        for check in failed_checks[:2]:
            check_name = check['check']
            if 'DPD' in check_name or 'Arrears' in check_name:
                issues.append("loan arrears exceeding 3 days, requiring a 60-day cooling period")
            elif 'Turnover' in check_name:
                issues.append("inconsistent credit turnovers and insufficient banking activity")
            elif 'vintage' in check_name:
                issues.append("insufficient banking relationship duration (less than 6 months)")
            elif 'Active' in check_name:
                issues.append("inactive account or mobile banking profile")
            else:
                issues.append(check['description'][:50])
        
        action_list = "\n".join([f"{i+1}. {action}" for i, action in enumerate(actions[:3])])
        
        return f"""Write a professional banking response. Do not create a conversation. Do not use dialogue format.

FACTS:
- Customer: {customer_name}
- ID: {customer_id}
- Status: NOT ELIGIBLE
- Issues: {', '.join(issues)}
- Next review: {next_review}

REQUIRED FORMAT - Write EXACTLY this structure:

Hello,

The customer {customer_name} is currently not eligible for a loan limit.

This is due to:
{action_list}

They may reapply after {next_review}.

Write only this format. Do not add conversations. Do not add Customer: or Banking: labels."""
    
    def _call_llm(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Very low temperature for consistency
                "num_predict": 200,   # Shorter responses
                "top_p": 0.5,         # More focused
                "repeat_penalty": 1.2, # Prevent repetition
                "stop": ["Customer:", "Banking:", "Q:", "A:"]  # Stop on dialogue markers
            }
        }
        
        response = requests.post(self.ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def _clean_response(self, response: str) -> str:
        # Remove any system artifacts
        response = response.strip()
        
        # Remove common LLM artifacts
        for artifact in ["Assistant:", "Response:", "Banking:", "Customer:", "Q:", "A:"]:
            response = response.replace(artifact, "")
        
        # Remove dialogue markers
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like dialogue
            if line.startswith(('Customer:', 'Banking:', 'Q:', 'A:')):
                continue
            if line:
                cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        
        # Take only first few paragraphs if it's too long
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 4:
            response = '\n\n'.join(paragraphs[:4])
        
        return response.strip()
    
    def _fallback_response(self, result: Dict) -> str:
        """Enhanced template-based response if LLM fails"""
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        
        if status == "Include":
            return f"Good news! {customer_name} (ID: {customer_id}) is eligible for an LFA loan. All eligibility checks have passed and they can proceed with their application."
        
        failed = result.get('failed_checks', [])
        if not failed:
            return f"{customer_name} (ID: {customer_id}) - Status: {status}"
        
        next_review = result.get('next_review_date', 'Unknown')
        actions = result.get('actions', [])
        
        # Build structured response
        action_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(actions[:3])])
        
        return f"""Hello,

The customer {customer_name} (ID: {customer_id}) is currently not eligible for a loan limit.

This is due to:
{action_text}

They may reapply after {next_review}."""

generator = ResponseGenerator()