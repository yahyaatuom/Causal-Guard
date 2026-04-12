# test_nvidia.py
from llm_interface import GroqLLM
from dotenv import load_dotenv
import os

# Force load from specific path
env_path = r"C:\Users\Dell\Desktop\Causal-Guard\.env"
load_dotenv(env_path)

# Debug: Check if key is loaded
api_key = os.getenv("NVIDIA_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"Key starts with: {api_key[:15] if api_key else 'None'}...")

llm = GroqLLM()
response = llm.generate_explanation("Test incident: Car crashed due to wet road.")
print(response['explanation'])
print(response['tokens'])