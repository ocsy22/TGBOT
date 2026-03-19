"""
Telegram消息发送模块 - 支持Bot API和MTProto
"""
import os
import asyncio
import json
import aiohttp


class TelegramSender:
    """Telegram消息发送器"""

    def __init__(self, config: dict):
        self.config = config
        self.local_bot_api = config.get('local_bot_api', '')

    async def send_via_bot(self, token: str, chat_id: str,
                           text: str = '', video_path: str = '',
                           photo_paths: list = None,
                           caption: str = '',
                           parse_mode: str = 'HTML',
                           disable_notification: bool = False,
                           progress_callback=None) -> dict:
        """通过Bot API发送消息"""
        if not token:
            return {'success': False, 'error': 'Bot Token未配置'}

        base_url = self.local_bot_api or 'https://api.telegram.org'
        api_base = f'{base_url}/bot{token}'

        try:
            async with aiohttp.ClientSession() as session:
                # 发送视频
                if video_path and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    if file_size > 50 * 1024 * 1024 and not self.local_bot_api:
                        return {
                            'success': False,
                            'error': f'文件大于50MB({file_size/1024/1024:.1f}MB)，请使用MTProto账号发送'
                        }

                    form = aiohttp.FormData()
                    form.add_field('chat_id', str(chat_id))
                    form.add_field('parse_mode', parse_mode)
                    if disable_notification:
                        form.add_field('disable_notification', 'true')
                    if caption:
                        form.add_field('caption', caption[:1024])

                    with open(video_path, 'rb') as f:
                        form.add_field('video', f, filename=os.path.basename(video_path))
                        async with session.post(
                            f'{api_base}/sendVideo', data=form,
                            timeout=aiohttp.ClientTimeout(total=300)
                        ) as resp:
                            result = await resp.json()
                            return {'success': result.get('ok', False),
                                    'error': result.get('description', '')}

                # 发送图片组
                elif photo_paths:
                    media = []
                    files = {}
                    for i, path in enumerate(photo_paths[:10]):
                        if os.path.exists(path):
                            media.append({
                                'type': 'photo',
                                'media': f'attach://photo{i}',
                                **({"caption": caption, "parse_mode": parse_mode} if i == 0 and caption else {})
                            })
                            files[f'photo{i}'] = open(path, 'rb')

                    form = aiohttp.FormData()
                    form.add_field('chat_id', str(chat_id))
                    form.add_field('media', json.dumps(media))
                    if disable_notification:
                        form.add_field('disable_notification', 'true')
                    for k, f in files.items():
                        form.add_field(k, f.read(), filename=os.path.basename(f.name), content_type='image/jpeg')
                    for f in files.values():
                        f.close()

                    async with session.post(
                        f'{api_base}/sendMediaGroup', data=form,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as resp:
                        result = await resp.json()
                        return {'success': result.get('ok', False),
                                'error': result.get('description', '')}

                # 纯文本
                elif text:
                    payload = {
                        'chat_id': chat_id,
                        'text': text[:4096],
                        'parse_mode': parse_mode,
                        'disable_notification': disable_notification,
                    }
                    async with session.post(
                        f'{api_base}/sendMessage', json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        result = await resp.json()
                        return {'success': result.get('ok', False),
                                'error': result.get('description', '')}

                return {'success': False, 'error': '没有内容可发送'}

        except asyncio.TimeoutError:
            return {'success': False, 'error': '发送超时，请检查网络连接'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def send_via_mtproto(self, api_id: int, api_hash: str,
                                session_string: str, phone: str,
                                chat_id: str, text: str = '',
                                file_path: str = '', caption: str = '') -> dict:
        """通过MTProto发送（支持2GB大文件）"""
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            client = TelegramClient(
                StringSession(session_string) if session_string else StringSession(),
                int(api_id), api_hash
            )
            await client.connect()

            if not await client.is_user_authorized():
                return {'success': False, 'error': '账号未授权，请先完成登录验证'}

            if file_path and os.path.exists(file_path):
                await client.send_file(chat_id, file_path, caption=caption)
            elif text:
                await client.send_message(chat_id, text)

            await client.disconnect()
            return {'success': True}

        except ImportError:
            return {'success': False, 'error': 'telethon未安装'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
