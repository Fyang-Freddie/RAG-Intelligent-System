import requests
import json
import os
from typing import Dict
from app.config import HKGAI_API_KEY

class HKGAIClient:
    """Client for HKGAI API integration"""
    def __init__(self):
        self.base_url = "https://oneapi.hkgai.net/v1"
        self.api_key = HKGAI_API_KEY
        self.model_id = "HKGAI-V1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Dict:
        """Send chat completion request to HKGAI API"""
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

        data = response.json()
        content = ""
        try:
            choices = data.get("choices", [])
            if choices:
                first = choices[0] if isinstance(choices[0], dict) else {}
                message = first.get("message") or {}
                content = (message.get("content") or "").strip()
                if not content:
                    content = (first.get("text") or "").strip()
        except Exception:
            pass

        if not content:
            return {
                "content": "",
                "warning": "Empty content returned",
                "raw": data
            }

        return {"content": content, "raw": data}