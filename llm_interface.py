# llm_interface.py
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

class GroqLLM:
    def __init__(self, model="llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("⚠️ Error: GROQ_API_KEY not found. Check your .env file.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = 0

    def generate_explanation(self, scenario_description):
        """
        Send scenario to Groq and get explanation.
        """
        if not self.client:
            return {
                'explanation': "Error: API key not configured",
                'model': self.model,
                'tokens': {'prompt': 0, 'completion': 0}
            }
        
        prompt = f"""You are an expert in urban transportation and causal reasoning.
Analyze the following incident and provide a concise explanation focusing on the scenario.

Incident: {scenario_description}

Explanation:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=500
            )
            
            return {
                'explanation': response.choices[0].message.content,
                'model': self.model,
                'tokens': {
                    'prompt': response.usage.prompt_tokens,
                    'completion': response.usage.completion_tokens,
                    'total': response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                'explanation': f"Error: {str(e)}",
                'model': self.model,
                'tokens': {'prompt': 0, 'completion': 0}
            }