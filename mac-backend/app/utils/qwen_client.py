import base64

from openai import OpenAI


class QwenAPIClient:
    def __init__(self, vision_model: str, text_model: str, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("Missing Qwen API key")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.vision_model = vision_model
        self.text_model = text_model

    @staticmethod
    def encode_image_bytes(image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{content_type};base64,{base64_str}"

    def call_vision(
        self,
        prompt: str,
        image_data_url: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def call_text(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.text_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
