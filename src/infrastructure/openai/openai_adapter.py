from openai import OpenAI
from src.domain.ports import AIPort 

class OpenAIAdapter(AIPort):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("The OpenAI API KEY is missing from the adapter.")
        self.client = OpenAI(api_key=api_key)

    def generate_report(self, system_prompt: str, user_json_data: str, model: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_json_data}
                ],
                temperature=0.1, 
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI Adapter Error: {str(e)}")