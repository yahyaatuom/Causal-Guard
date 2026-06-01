from llm_interface import GroqLLM

llm = GroqLLM()

result = llm.generate_explanation("Car crashed on wet road due to children spilling some water on it")
print(result['explanation'])
print(result['tokens'])