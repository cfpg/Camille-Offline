import logging
from typing import List, Dict
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, model: str, api_base: str, api_key: str):
        self.model = model
        self.api_base = api_base
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def get_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
