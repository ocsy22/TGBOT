"""
Telegram发送模块 - 支持Bot API和MTProto账号发送
"""
import os
import asyncio
import json
import time
from pathlib import Path


class TelegramSender:
    """Telegram消息发送器"""

    def __init__(self, config: dict):
        self.config = config
        self.mtproto_proxy = config.get('mtproto_proxy', '')
        self.local_bot_api = config.get('local_bot_api', '')

    # =================== Bot API发送 ===================

    async def send_via_bot(self, token: str, chat_id: str,
                           text: str = '', video_path: str = '',
                           photo_paths: list = None,
                           caption: str = '',
                           parse_mode: str = 'HTML',
                           disable_notification: bool = False,
                           progress_callback=None) -> dict:
        """通过Bot API发送消息"""
        import aiohttp

        base_url = self.local_bot_api or 'https://api.telegram.org'
        api_base = f'{base_url}/bot{token}'

        try:
            async with aiohttp.ClientSession() as session:
                # 发送视频
                if video_path and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)

                    if file_size > 50 * 1024 * 1024 and not self.local_bot_api:
                        # 大文件需要本地Bot API或MTProto
                        return {
                            'success': False,
                            'error': f'文件大于50MB({file_size/1024/1024:.1f}MB)，需要配置本地Bot API或使用MTProto账号发送'
                        }

                    # 准备发送视频
                    form = aiohttp.FormData()
                    form.add_field('chat_id', str(chat_id))
                    form.add_field('parse_mode', parse_mode)
                    if disable_notification:
                        form.add_field('disable_notification', 'true')

                    if caption:
                        form.add_field('caption', caption)

                    with open(video_path, 'rb') as f:
                        form.add_field('video', f, filename=os.path.basename(video_path))
                        async with session.post(f'{api_base}/sendVideo', data=form, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                            result = await resp.json()
                            if result.get('ok'):
                                return {'success': True, 'result': result}
                            else:
                                return {'success': False, 'error': result.get('description', 'Unknown error')}

                # 发送图片组（媒体组）
                elif photo_paths:
                    media = []
                    for i, path in enumerate(photo_paths[:10]):
                        media_item = {
                            'type': 'photo',
                            'media': f'attach://photo{i}'
                        }
                        if i == 0 and caption:
                            media_item['caption'] = caption
                            media_item['parse_mode'] = parse_mode
                        media.append(media_item)

                    form = aiohttp.FormData()
                    form.add_field('chat_id', str(chat_id))
                    form.add_field('media', json.dumps(media))
                    if disable_notification:
                        form.add_field('disable_notification', 'true')

                    for i, path in enumerate(photo_paths[:10]):
                        if os.path.exists(path):
                            with open(path, 'rb') as f:
                                form.add_field(f'photo{i}', f.read(), filename=os.path.basename(path), content_type='image/jpeg')

                    async with session.post(f'{api_base}/sendMediaGroup', data=form, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                        result = await resp.json()
                        if result.get('ok'):
                            return {'success': True, 'result': result}
                        else:
                            return {'success': False, 'error': result.get('description', 'Unknown error')}

                # 纯文本消息
                elif text:
                    payload = {
                        'chat_id': chat_id,
                        'text': text,
                        'parse_mode': parse_mode,
                        'disable_notification': disable_notification
                    }
                    async with session.post(f'{api_base}/sendMessage', json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        result = await resp.json()
                        if result.get('ok'):
                            return {'success': True, 'result': result}
                        else:
                            return {'success': False, 'error': result.get('description', 'Unknown error')}

                return {'success': False, 'error': '没有要发送的内容'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_bot_channels(self, token: str) -> list:
        """获取Bot管理的频道列表"""
        import aiohttp
        base_url = self.local_bot_api or 'https://api.telegram.org'
        api_base = f'{base_url}/bot{token}'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{api_base}/getMe', timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.json()
                    if result.get('ok'):
                        return [{'bot_info': result['result']}]
            return []
        except:
            return []

    # =================== MTProto账号发送 ===================

    async def send_via_account(self, phone: str, api_id: int, api_hash: str,
                               session_string: str, chat_id: str,
                               text: str = '', video_path: str = '',
                               photo_paths: list = None,
                               caption: str = '',
                               parse_mode: str = 'html',
                               progress_callback=None,
                               proxy=None) -> dict:
        """通过MTProto账号发送消息（支持2GB大文件）"""
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            from telethon.tl.types import InputPeerChannel, DocumentAttributeVideo

            proxy_config = None
            if proxy:
                # 解析 socks5://ip:port 格式
                import socks
                if proxy.startswith('socks5://'):
                    parts = proxy.replace('socks5://', '').split(':')
                    proxy_config = (socks.SOCKS5, parts[0], int(parts[1]))

            client = TelegramClient(
                StringSession(session_string) if session_string else StringSession(),
                api_id, api_hash,
                proxy=proxy_config
            )

            await client.start(phone=phone)

            try:
                entity = await client.get_entity(chat_id)

                if video_path and os.path.exists(video_path):
                    # 发送视频文件（支持最大2GB）
                    result = await client.send_file(
                        entity,
                        video_path,
                        caption=caption,
                        parse_mode=parse_mode,
                        supports_streaming=True,
                        progress_callback=progress_callback
                    )
                elif photo_paths:
                    # 发送图片组
                    existing = [p for p in photo_paths if os.path.exists(p)]
                    result = await client.send_file(
                        entity, existing,
                        caption=caption,
                        parse_mode=parse_mode
                    )
                elif text:
                    result = await client.send_message(entity, text, parse_mode=parse_mode)
                else:
                    return {'success': False, 'error': '没有要发送的内容'}

                # 保存session
                new_session = client.session.save()
                return {'success': True, 'result': str(result.id), 'session': new_session}

            finally:
                await client.disconnect()

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def login_account(self, phone: str, api_id: int, api_hash: str,
                            proxy=None) -> dict:
        """登录Telegram账号，返回session字符串"""
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.connect()

            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                return {'success': True, 'status': 'code_required', 'client': client}

            session = client.session.save()
            await client.disconnect()
            return {'success': True, 'status': 'logged_in', 'session': session}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # =================== 工具方法 ===================

    def run_async(self, coro):
        """在同步环境中运行异步代码"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def send_sync(self, **kwargs) -> dict:
        """同步发送（自动选择Bot或账号）"""
        mode = kwargs.pop('mode', 'bot')
        if mode == 'bot':
            return self.run_async(self.send_via_bot(**kwargs))
        else:
            return self.run_async(self.send_via_account(**kwargs))
