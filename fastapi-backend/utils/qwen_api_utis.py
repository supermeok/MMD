import base64
import os
from openai import OpenAI

class QwenVLAPI:
    def __init__(self, model_name='qwen_vl_plus', api_key=None, base_url=None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or os.getenv("base_url")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model_name

    @staticmethod
    def encode_image_bytes(image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        """将图片字节编码为 Data URL 字符串"""
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{content_type};base64,{base64_str}"

    def call(self, prompt, image_data_url=None, temperature=0.0, max_tokens=512):
        try:
            if image_data_url:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            else:
                messages = [{"role": "user", "content": prompt}]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            raise

def call_qwen_vl_api(prompt, image_data_url, api_client, temperature=0.0, max_tokens=512):
    return api_client.call(prompt, image_data_url, temperature, max_tokens)

def call_qwen_text_api(prompt, api_client, temperature=0.0, max_tokens=512):
    return api_client.call(prompt, temperature=temperature, max_tokens=max_tokens)