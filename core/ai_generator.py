"""
AI文案生成模块 - 支持多家AI服务商（含成人内容）
"""
import asyncio
import aiohttp
import requests


AI_PRESETS = {
    "Grok (xAI)": {
        "api_url": "https://api.x.ai/v1",
        "text_model": "grok-3-mini",
        "vision_model": "grok-2-vision-1212",
        "note": "xAI Grok - 支持成人内容，免费额度充足"
    },
    "DeepSeek": {
        "api_url": "https://api.deepseek.com/v1",
        "text_model": "deepseek-chat",
        "vision_model": "deepseek-chat",
        "note": "DeepSeek - 中文优化，性价比高"
    },
    "Together AI": {
        "api_url": "https://api.together.xyz/v1",
        "text_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "vision_model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "note": "Together AI - 开源模型，无内容审查"
    },
    "Groq": {
        "api_url": "https://api.groq.com/openai/v1",
        "text_model": "llama-3.3-70b-versatile",
        "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "note": "Groq - 极速推理，免费额度"
    },
    "Gemini": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "text_model": "gemini-2.0-flash",
        "vision_model": "gemini-2.0-flash",
        "note": "Google Gemini - 免费额度丰富"
    },
    "Mistral": {
        "api_url": "https://api.mistral.ai/v1",
        "text_model": "mistral-small-latest",
        "vision_model": "pixtral-12b-2409",
        "note": "Mistral - 欧洲模型，内容政策宽松"
    },
    "OpenAI": {
        "api_url": "https://api.openai.com/v1",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
        "note": "OpenAI官方"
    },
    "Claude": {
        "api_url": "https://api.anthropic.com/v1",
        "text_model": "claude-3-5-haiku-20241022",
        "vision_model": "claude-3-5-sonnet-20241022",
        "note": "Anthropic Claude"
    },
    "SambaNova": {
        "api_url": "https://api.sambanova.ai/v1",
        "text_model": "Meta-Llama-3.3-70B-Instruct",
        "vision_model": "Llama-3.2-11B-Vision-Instruct",
        "note": "SambaNova - 免费高速"
    },
    "Cohere": {
        "api_url": "https://api.cohere.com/compatibility/v1",
        "text_model": "command-r-plus-08-2024",
        "vision_model": "command-r-plus-08-2024",
        "note": "Cohere - 企业级"
    },
    "小悟SaaS": {
        "api_url": "https://api.xiaowu.ai/v1",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
        "note": "小悟SaaS - 国内无内容限制"
    },
    "自定义": {
        "api_url": "",
        "text_model": "",
        "vision_model": "",
        "note": "自定义OpenAI兼容API"
    }
}


class AIGenerator:
    """AI文案生成器"""

    def __init__(self, config: dict):
        self.api_url = config.get('api_url', '').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.text_model = config.get('text_model', 'gpt-4o-mini')
        self.vision_model = config.get('vision_model', 'gpt-4o')
        self.max_tokens = config.get('max_tokens', 1024)
        self.http_proxy = config.get('http_proxy', '')

    async def generate_text(self, prompt: str, system_prompt: str = '') -> str:
        """生成文本"""
        if not self.api_key:
            raise ValueError("API Key未配置")
        if not self.api_url:
            raise ValueError("API URL未配置")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.text_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.8,
        }

        proxy = self.http_proxy or None

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"API错误 {resp.status}: {error_text[:300]}")
                data = await resp.json()
                return data['choices'][0]['message']['content'].strip()

    def generate_text_sync(self, prompt: str, system_prompt: str = '') -> str:
        """同步版本"""
        return asyncio.run(self.generate_text(prompt, system_prompt))
