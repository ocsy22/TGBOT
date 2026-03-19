"""
任务执行引擎 - 处理视频裁剪、文案生成、发布等完整流程
"""
import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path

from .database import DB
from .ai_generator import AIGenerator
from .video_processor import VideoProcessor
from .telegram_sender import TelegramSender


class TaskEngine:
    """任务执行引擎"""

    def __init__(self):
        self._running_tasks = {}
        self._lock = threading.Lock()

    def execute_task(self, task_id: int, progress_callback=None, log_callback=None):
        """执行单个任务"""
        task = DB.fetchone('SELECT * FROM tasks WHERE id=?', (task_id,))
        if not task:
            return False

        def log(msg):
            if log_callback:
                log_callback(msg)

        def progress(pct):
            DB.execute('UPDATE tasks SET progress=? WHERE id=?', (pct, task_id))
            if progress_callback:
                progress_callback(pct)

        try:
            DB.execute("UPDATE tasks SET status='processing', progress=0 WHERE id=?", (task_id,))
            log(f'🚀 开始执行任务 #{task_id}')

            # 加载配置
            ai_cfg = DB.fetchone('SELECT * FROM ai_settings WHERE id=1')
            video_cfg = DB.fetchone('SELECT * FROM video_settings WHERE id=1')
            pub_cfg = DB.fetchone('SELECT * FROM publish_settings WHERE id=1')

            # 获取要发布的频道
            channel_ids = json.loads(task.get('channel_ids', '[]'))
            channels = [DB.fetchone('SELECT * FROM channels WHERE id=?', (cid,)) for cid in channel_ids]
            channels = [c for c in channels if c]

            if not channels:
                raise Exception('没有选择发布频道')

            # 处理媒体文件
            video_path = ''
            clipped_video = ''
            screenshot_path = ''
            media_file_id = task.get('media_file_id', 0)

            if media_file_id:
                media = DB.fetchone('SELECT * FROM media_files WHERE id=?', (media_file_id,))
                if media:
                    video_path = media.get('filepath', '')

            # 视频裁剪
            if task.get('clip_enabled') and video_path and os.path.exists(video_path):
                log('✂️ 开始裁剪视频...')
                progress(10)

                vp = VideoProcessor(video_cfg.get('ffmpeg_path', 'ffmpeg'))
                input_dir = os.path.dirname(video_path)
                clip_output_dir = os.path.join(input_dir, '已裁剪')
                os.makedirs(clip_output_dir, exist_ok=True)

                base_name = os.path.splitext(os.path.basename(video_path))[0]
                clip_output = os.path.join(clip_output_dir, f'{base_name}_clipped.mp4')

                def clip_progress(pct):
                    progress(10 + int(pct * 0.3))

                success = vp.clip_video(
                    video_path, clip_output,
                    start=task.get('clip_start', 0),
                    duration=task.get('clip_duration', 60),
                    resolution=task.get('clip_resolution', '1920x1080'),
                    bitrate=task.get('clip_bitrate', '4M'),
                    encoder=video_cfg.get('encoder', 'libx264'),
                    progress_callback=clip_progress
                )

                if success:
                    clipped_video = clip_output
                    log(f'✅ 视频裁剪完成: {clip_output}')
                else:
                    log('⚠️ 视频裁剪失败，使用原始视频')
                    clipped_video = video_path
            else:
                clipped_video = video_path

            # 截图
            if task.get('screenshot_enabled') and video_path and os.path.exists(video_path):
                log('📸 提取视频截图...')
                progress(45)

                vp = VideoProcessor(video_cfg.get('ffmpeg_path', 'ffmpeg'))
                thumb_dir = os.path.join(os.path.dirname(video_path), 'thumbnails')

                screenshot_path = vp.extract_screenshots(
                    video_path, thumb_dir,
                    grid=video_cfg.get('cover_grid', '3x3'),
                    size=video_cfg.get('cover_size', 1080)
                )
                if screenshot_path:
                    log(f'✅ 截图完成: {screenshot_path}')
                else:
                    log('⚠️ 截图提取失败')

            # 获取视频时长
            duration_str = ''
            if video_path and os.path.exists(video_path):
                vp = VideoProcessor(video_cfg.get('ffmpeg_path', 'ffmpeg'))
                info = vp.get_video_info(video_path)
                duration_str = vp.format_duration(info.get('duration', 0))

            # AI生成文案
            final_text = ''
            if task.get('ai_generate'):
                log('🤖 AI生成文案...')
                progress(55)

                ai = AIGenerator(ai_cfg)

                # 获取写作方向
                direction = None
                wd_id = task.get('writing_direction_id', 0)
                if wd_id:
                    direction = DB.fetchone('SELECT * FROM writing_directions WHERE id=?', (wd_id,))

                # 分析视频内容
                video_desc = ''
                if screenshot_path and os.path.exists(screenshot_path) and ai_cfg.get('vision_model'):
                    try:
                        video_desc = ai.analyze_video_with_vision(screenshot_path)
                        log(f'👁️ 视觉分析: {video_desc[:50]}...')
                    except:
                        pass

                # 生成文案
                if video_desc:
                    copy_data = ai.generate_from_video_analysis(video_desc, direction)
                else:
                    title = task.get('title', '') or os.path.splitext(os.path.basename(video_path or 'video'))[0]
                    copy_data = ai.generate_from_title(title, direction)

                if 'error' not in copy_data:
                    # 应用模板
                    template = '<b>{title}</b>\n{content}\n⏱ 时长: {duration}'
                    tmpl_id = task.get('copy_template_id', 0)
                    if tmpl_id:
                        tmpl = DB.fetchone('SELECT template FROM copy_templates WHERE id=?', (tmpl_id,))
                        if tmpl:
                            template = tmpl['template']

                    final_text = ai.format_copy(
                        template,
                        copy_data.get('title', ''),
                        copy_data.get('content', ''),
                        duration_str,
                        copy_data.get('emoji', '🔥')
                    )

                    # 添加标签
                    tags = copy_data.get('tags', [])
                    tag_str = DB.fetchone('SELECT tag_library FROM publish_settings WHERE id=1')
                    if tag_str and tag_str.get('tag_library'):
                        library_tags = json.loads(tag_str['tag_library'])
                        if library_tags:
                            import random
                            selected = random.sample(library_tags, min(5, len(library_tags)))
                            tags = list(set(tags + selected))

                    if tags:
                        final_text += '\n' + ' '.join(f'#{t.lstrip("#")}' for t in tags[:8])

                    # 添加尾部链接
                    footer = DB.fetchone('SELECT footer_links FROM publish_settings WHERE id=1')
                    if footer and footer.get('footer_links'):
                        links = json.loads(footer['footer_links'])
                        for link in links:
                            final_text += f"\n{link.get('text', '')} {link.get('url', '')}"

                    log(f'✅ 文案生成完成')
                    DB.execute('UPDATE tasks SET result_text=? WHERE id=?', (final_text, task_id))

            progress(70)

            # 发布到各频道
            log('📤 开始发布到频道...')
            sender = TelegramSender({
                'mtproto_proxy': pub_cfg.get('mtproto_proxy', '') if pub_cfg else '',
                'local_bot_api': pub_cfg.get('local_bot_api', '') if pub_cfg else ''
            })

            success_count = 0
            fail_count = 0

            for ch in channels:
                log(f'📢 发布到: {ch["name"]}')

                # 构建发送参数
                send_video = clipped_video if clipped_video else video_path
                photos = [screenshot_path] if screenshot_path and not send_video else []

                if ch.get('send_mode', 'bot') == 'bot' and ch.get('bot_id'):
                    bot = DB.fetchone('SELECT * FROM bots WHERE id=?', (ch['bot_id'],))
                    if not bot:
                        log(f'❌ Bot不存在: {ch["name"]}')
                        fail_count += 1
                        continue

                    import asyncio
                    result = asyncio.run(sender.send_via_bot(
                        token=bot['token'],
                        chat_id=ch.get('chat_id') or ch.get('username'),
                        text=final_text if not send_video else '',
                        video_path=send_video,
                        photo_paths=photos if not send_video else None,
                        caption=final_text if send_video else ''
                    ))
                else:
                    # MTProto账号发送
                    account = DB.fetchone('SELECT * FROM accounts WHERE id=?', (ch.get('account_id', 0),))
                    if not account:
                        log(f'❌ 账号不存在: {ch["name"]}')
                        fail_count += 1
                        continue

                    api_info = DB.fetchone('SELECT * FROM telegram_apis WHERE id=?', (account.get('api_id', 0),))
                    if not api_info:
                        log(f'❌ API配置不存在')
                        fail_count += 1
                        continue

                    import asyncio
                    result = asyncio.run(sender.send_via_account(
                        phone=account['phone'],
                        api_id=int(api_info['api_id']),
                        api_hash=api_info['api_hash'],
                        session_string=account.get('session_string', ''),
                        chat_id=ch.get('chat_id') or ch.get('username'),
                        text=final_text if not send_video else '',
                        video_path=send_video,
                        photo_paths=photos if not send_video else None,
                        caption=final_text if send_video else ''
                    ))

                if result.get('success'):
                    success_count += 1
                    log(f'✅ 发布成功: {ch["name"]}')
                    # 记录日志
                    DB.execute(
                        'INSERT INTO publish_logs (task_id, channel_id, channel_name, status, message) VALUES (?,?,?,?,?)',
                        (task_id, ch['id'], ch['name'], 'success', '发布成功')
                    )
                    # 自动点赞
                    if ch.get('auto_like'):
                        pass  # TODO
                else:
                    fail_count += 1
                    error = result.get('error', '未知错误')
                    log(f'❌ 发布失败 {ch["name"]}: {error}')
                    DB.execute(
                        'INSERT INTO publish_logs (task_id, channel_id, channel_name, status, message) VALUES (?,?,?,?,?)',
                        (task_id, ch['id'], ch['name'], 'failed', error)
                    )

                time.sleep(1)  # 避免频率限制

            progress(100)
            status = 'completed' if fail_count == 0 else ('partial' if success_count > 0 else 'failed')
            DB.execute(
                "UPDATE tasks SET status=?, finished_at=? WHERE id=?",
                (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task_id)
            )
            log(f'🎉 任务完成！成功: {success_count}, 失败: {fail_count}')
            return True

        except Exception as e:
            DB.execute(
                "UPDATE tasks SET status='failed', error_msg=? WHERE id=?",
                (str(e), task_id)
            )
            log(f'❌ 任务失败: {e}')
            return False

    def execute_task_async(self, task_id: int, progress_callback=None, log_callback=None):
        """异步执行任务"""
        t = threading.Thread(
            target=self.execute_task,
            args=(task_id, progress_callback, log_callback),
            daemon=True
        )
        t.start()
        with self._lock:
            self._running_tasks[task_id] = t
        return t
