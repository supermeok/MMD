from app.utils.qwen_client import QwenAPIClient


class QwenVLAPI(QwenAPIClient):
    def __init__(self, model_name='qwen3.5-plus', api_key=None, base_url=None):
        super().__init__(
            vision_model=model_name,
            text_model=model_name,
            api_key=api_key,
            base_url=base_url,
        )

    def call(self, prompt, image_data_url=None, temperature=0.0, max_tokens=512):
        if image_data_url:
            return self.call_vision(prompt, image_data_url, temperature=temperature, max_tokens=max_tokens)
        return self.call_text(prompt, temperature=temperature, max_tokens=max_tokens)


def call_qwen_vl_api(prompt, image_data_url, api_client, temperature=0.0, max_tokens=512):
    return api_client.call(prompt, image_data_url, temperature, max_tokens)


def call_qwen_text_api(prompt, api_client, temperature=0.0, max_tokens=512):
    return api_client.call(prompt, temperature=temperature, max_tokens=max_tokens)
