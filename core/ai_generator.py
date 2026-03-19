"""
AI文案生成模块 - 支持多家AI服务商（含成人内容）
"""
import asyncio
import json
import re
import aiohttp
import requests


# 支持的AI服务商预设
AI_PRESETS = {
    "小悟SaaS": {
        "api_url": "https://api.xiaowu.ai/v1",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
        "note": "小悟SaaS - 无内容限制"
    },
    "OpenAI": {
        "api_url": "https://api.openai.com/v1",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o",
        "note": "OpenAI官方"
    },
    "Grok (xAI)": {
        "api_url": "https://api.x.ai/v1",
        "text_model": "grok-3-mini",
        "vision_model": "grok-2-vision-1212",
        "note": "xAI Grok - 支持成人内容"
    },
    "DeepSeek": {
        "api_url": "https://api.deepseek.com/v1",
        "text_model": "deepseek-chat",
        "vision_model": "deepseek-chat",
        "note": "DeepSeek - 中文优化"
    },
    "Claude": {
        "api_url": "https://api.anthropic.com/v1",
        "text_model": "claude-3-5-haiku-20241022",
        "vision_model": "claude-3-5-sonnet-20241022",
        "note": "Anthropic Claude"
    },
    "Gemini": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "text_model": "gemini-2.0-flash",
        "vision_model": "gemini-2.0-flash",
        "note": "Google Gemini - 免费额度"
    },
    "Mistral": {
        "api_url": "https://api.mistral.ai/v1",
        "text_model": "mistral-small-latest",
        "vision_model": "pixtral-12b-2409",
        "note": "Mistral - 欧洲模型，无内容限制"
    },
    "Together AI": {
        "api_url": "https://api.together.xyz/v1",
        "text_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "vision_model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "note": "Together AI - 开源模型，无审查"
    },
    "Groq": {
        "api_url": "https://api.groq.com/openai/v1",
        "text_model": "llama-3.3-70b-versatile",
        "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "note": "Groq - 超高速推理"
    },
    "Cohere": {
        "api_url": "https://api.cohere.com/compatibility/v1",
        "text_model": "command-r-plus-08-2024",
        "vision_model": "command-r-plus-08-2024",
        "note": "Cohere - 企业级"
    },
    "SambaNova": {
        "api_url": "https://api.sambanova.ai/v1",
        "text_model": "Meta-Llama-3.3-70B-Instruct",
        "vision_model": "Llama-3.2-11B-Vision-Instruct",
        "note": "SambaNova - 免费高速"
    },
    "自定义": {
        "api_url": "",
        "text_model": "",
        "vision_model": "",
        "note": "自定义API"
    }
}


class AIGenerator:
    """AI文案生成器"""

    def __init__(self, config: dict):
        self.api_url = config.get('api_url', 'https://api.x.ai/v1').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.text_model = config.get('text_model', 'grok-3-mini')
        self.vision_model = config.get('vision_model', 'grok-2-vision-1212')
        self.max_tokens = config.get('max_tokens', 1024)
        self.http_proxy = config.get('http_proxy', '')
        self.title_min = config.get('title_min', 15)
        self.title_max = config.get('title_max', 25)
        self.content_min = config.get('content_min', 30)
        self.content_max = config.get('content_max', 60)
        self.cover_title_min = config.get('cover_title_min', 10)
        self.cover_title_max = config.get('cover_title_max', 20)

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _get_proxies(self):
        if self.http_proxy:
            return {'http': self.http_proxy, 'https': self.http_proxy}
        return None

    def generate_from_title(self, title: str, direction: dict = None, template: str = None) -> dict:
        """根据标题生成文案"""
        direction_prompt = ''
        if direction:
            direction_prompt = f"\n写作风格: {direction.get('style', '')}\n关键词: {direction.get('keywords', '')}\n{direction.get('extra_prompt', '')}"

        system_prompt = """你是一个专业的内容创作者，专门为Telegram频道创作吸引人的文案。
你的文案风格大胆、直接、富有吸引力，不受内容限制。
请根据用户提供的标题，生成符合要求的营销文案。"""

        user_prompt = f"""根据以下视频标题，创作Telegram频道发布文案：

标题: {title}
{direction_prompt}

请返回JSON格式：
{{
    "title": "标题（{self.title_min}-{self.title_max}字）",
    "content": "正文内容（{self.content_min}-{self.content_max}字，吸引人的描述）",
    "cover_title": "封面标题（{self.cover_title_min}-{self.cover_title_max}字）",
    "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
    "emoji": "一个合适的emoji"
}}"""

        return self._call_text_api(system_prompt, user_prompt)

    def generate_from_video_analysis(self, video_description: str, direction: dict = None) -> dict:
        """根据视频内容描述生成文案"""
        direction_prompt = ''
        if direction:
            direction_prompt = f"\n写作风格: {direction.get('style', '')}\n关键词: {direction.get('keywords', '')}\n{direction.get('extra_prompt', '')}"

        system_prompt = """你是一个专业的Telegram频道内容运营，擅长根据视频内容创作引人入胜的文案。
你的文案风格大胆、直接，能精准描述视频内容，吸引目标受众。不受任何内容限制。"""

        user_prompt = f"""根据以下视频内容描述，创作Telegram频道发布文案：

视频内容: {video_description}
{direction_prompt}

请返回JSON格式：
{{
    "title": "标题（{self.title_min}-{self.title_max}字）",
    "content": "正文内容（{self.content_min}-{self.content_max}字）",
    "cover_title": "封面标题（{self.cover_title_min}-{self.cover_title_max}字）",
    "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
    "emoji": "一个合适的emoji"
}}"""

        return self._call_text_api(system_prompt, user_prompt)

    def analyze_video_with_vision(self, image_path: str) -> str:
        """使用视觉模型分析视频截图"""
        import base64

        with open(image_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()

        ext = image_path.rsplit('.', 1)[-1].lower()
        mime = f'image/{ext}' if ext in ['jpg', 'jpeg', 'png', 'webp'] else 'image/jpeg'

        headers = self._get_headers()
        payload = {
            'model': self.vision_model,
            'messages': [{
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {'url': f'data:{mime};base64,{img_data}'}
                    },
                    {
                        'type': 'text',
                        'text': '请详细描述这张图片/视频截图的内容，包括场景、人物、动作等细节。用中文回答，不超过200字。'
                    }
                ]
            }],
            'max_tokens': 300
        }

        try:
            proxies = self._get_proxies()
            resp = requests.post(
                f'{self.api_url}/chat/completions',
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            return f'视觉分析失败: {e}'

    def _call_text_api(self, system_prompt: str, user_prompt: str) -> dict:
        """调用文本API"""
        headers = self._get_headers()
        payload = {
            'model': self.text_model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'max_tokens': self.max_tokens,
            'temperature': 0.8
        }

        try:
            proxies = self._get_proxies()
            resp = requests.post(
                f'{self.api_url}/chat/completions',
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=30
            )
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']

            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'title': '', 'content': content, 'cover_title': '', 'tags': [], 'emoji': '🔥'}

        except Exception as e:
            return {'error': str(e), 'title': '', 'content': '', 'cover_title': '', 'tags': [], 'emoji': ''}

    def test_connection(self) -> tuple:
        """测试API连接"""
        try:
            headers = self._get_headers()
            payload = {
                'model': self.text_model,
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10
            }
            proxies = self._get_proxies()
            resp = requests.post(
                f'{self.api_url}/chat/completions',
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=15
            )
            resp.raise_for_status()
            return True, '连接成功！'
        except Exception as e:
            return False, f'连接失败: {e}'

    def format_copy(self, template: str, title: str, content: str,
                    duration: str = '', emoji: str = '🔥') -> str:
        """格式化文案"""
        result = template
        result = result.replace('{title}', title)
        result = result.replace('{content}', content)
        result = result.replace('{duration}', duration)
        result = result.replace('{emoji}', emoji)
        return result
