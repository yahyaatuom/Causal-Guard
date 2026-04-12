# llm_interface.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Force load from the correct path
env_path = r"C:\Users\Dell\Desktop\Causal-Guard\.env"
load_dotenv(env_path)

class GroqLLM:
    def __init__(self, model="deepseek-ai/deepseek-r1-distill-qwen-7b"):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = model
        self.temperature = 0
        
        # Debug print
        print(f"DEBUG: API Key loaded: {'Yes' if self.api_key else 'No'}")
        
        if not self.api_key:
            print("⚠️ Error: NVIDIA_API_KEY not found. Check your .env file.")
            self.client = None
        else:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )

    
    def generate_explanation(self, scenario_description):
        """
        Send scenario to NVIDIA NIM and get explanation
        """
        if not self.client:
            return {
                'explanation': "Error: API key not configured",
                'model': self.model,
                'tokens': {'prompt': 0, 'completion': 0, 'total': 0}
            }
        
        prompt = f"""Analyze the following incident and provide a concise explanation focusing on the scenario.

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
                'tokens': {'prompt': 0, 'completion': 0, 'total': 0}
            }