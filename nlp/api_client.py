import logging
from typing import List, Dict, Optional, Any
import requests
from requests.exceptions import RequestException
from utils.log import print_log
from nlp.types import Tool

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, model: str, api_base: str, api_key: str):
        self.model = model
        self.api_base = api_base
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        try:
            print_log(f"Sending completion request to OpenAI API: {messages}", "magenta")
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
            
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
