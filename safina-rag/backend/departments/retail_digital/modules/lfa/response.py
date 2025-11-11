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
            print(f"[DEBUG] Raw LLM response: {response[:300]}")  # Debug output
            cleaned = self._clean_response(response)
            print(f"[DEBUG] Cleaned response: {cleaned[:300]}")  # Debug output
            
            # If cleaning removed everything, use fallback
            if not cleaned or len(cleaned) < 20:
                print("[DEBUG] Response too short after cleaning, using fallback")
                return self._fallback_response(eligibility_result)
            
            return cleaned
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            return self._fallback_response(eligibility_result)
    
    def _build_prompt(self, result: Dict, query: str) -> str:
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        failed_checks = result.get('failed_checks', [])
        actions = result.get('actions', [])
        
        if status == "Include":
            return f"""Write a brief professional message confirming loan eligibility.

Customer: {customer_name} (ID: {customer_id})

Write 2-3 sentences confirming they are eligible. Be direct and positive.
Do NOT use labels, dialogue format, or ask follow-up questions."""

        # Build specific issues from failed checks
        issues = []
        for check in failed_checks[:3]:
            check_name = check['check']
            desc = check.get('description', '')
            
            if 'DPD' in check_name or 'Arrears' in check_name:
                issues.append("Loan arrears exceeding 3 days within the past 60 days")
            elif 'Turnover' in check_name:
                issues.append("Insufficient or inconsistent account turnover")
            elif 'vintage' in check_name.lower():
                issues.append("Banking relationship less than 6 months")
            elif 'Active' in check_name or 'Inactive' in check_name:
                issues.append("Inactive account or mobile banking profile")
            elif 'Elma' in check_name:
                issues.append("Mobile banking not active or account already under review")
            elif 'Classification' in check_name or 'Risk' in check_name:
                issues.append("Risk classification below required threshold (A5)")
            else:
                issues.append(desc[:60] if desc else "Eligibility criteria not met")
        
        issues_text = "\n".join([f"• {issue}" for issue in issues])
        action_list = "\n".join([f"• {action}" for action in actions[:3]])
        
        return f"""Write a clear professional message explaining loan ineligibility.

Customer: {customer_name} (ID: {customer_id})
Status: NOT ELIGIBLE

Issues identified:
{issues_text}

Required actions:
{action_list}

Write 2-3 paragraphs explaining the situation clearly and professionally.
Do NOT use labels like "Response:" or "Customer:".
Do NOT ask follow-up questions or offer to summarize.
Do NOT mention review dates.
Be direct, factual, and supportive."""
    
    def _call_llm(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,     # Lower for more consistency
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "num_predict": 300,
                "stop": ["Customer:", "Banking:", "Q:", "A:", "Response:"]
            }
        }

        response = requests.post(self.ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def _clean_response(self, response: str) -> str:
        """Minimal cleaning to preserve LLM output"""
        if not response:
            return ""
        
        response = response.strip()
        
        # Remove only obvious system artifacts at the start
        artifacts = ["Assistant:", "Response:", "RESPONSE:", "Banking:", "Customer:", "Message:"]
        for artifact in artifacts:
            if response.startswith(artifact):
                response = response[len(artifact):].strip()
        
        # Remove any remaining artifact prefixes from lines
        lines = []
        for line in response.split('\n'):
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip lines that are ONLY artifacts (nothing after them)
            if any(line == artifact.rstrip(':') for artifact in artifacts):
                continue
            lines.append(line)
        
        return '\n'.join(lines).strip()
    
    def _fallback_response(self, result: Dict) -> str:
        """Template-based fallback using actual failed check data"""
        customer_name = result.get('customer_name', 'Customer')
        customer_id = result.get('customer_id', 'Unknown')
        status = result.get('overall_status', 'Unknown')
        
        if status == "Include":
            return f"{customer_name} (ID: {customer_id}) is eligible for an LFA loan. All eligibility checks have been successfully completed and they can proceed with their application."
        
        failed = result.get('failed_checks', [])
        actions = result.get('actions', [])
        
        # Build specific issues from actual failed checks
        issues = []
        for check in failed[:3]:
            check_name = check['check']
            if 'DPD' in check_name or 'Arrears' in check_name:
                issues.append("Loan arrears exceeding 3 days within the past 60 days")
            elif 'Turnover' in check_name:
                issues.append("Insufficient or inconsistent account turnover")
            elif 'vintage' in check_name.lower():
                issues.append("Banking relationship less than 6 months")
            elif 'Active' in check_name or 'Inactive' in check_name:
                issues.append("Inactive account or mobile banking profile")
            elif 'Classification' in check_name or 'Risk' in check_name:
                issues.append("Risk classification below required threshold")
            else:
                issues.append(check.get('description', 'Eligibility criteria not met')[:60])
        
        if not issues:
            issues = ["Eligibility criteria not met"]
        
        issues_text = "\n".join([f"• {issue}" for issue in issues])
        action_text = "\n".join([f"• {action}" for action in actions[:3]]) if actions else "Please contact support for guidance."
        
        return f"""{customer_name} (ID: {customer_id}) is currently not eligible for a loan limit.

Issues identified:
{issues_text}

Required actions:
{action_text}"""

generator = ResponseGenerator()