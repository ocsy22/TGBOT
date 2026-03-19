"""
视频处理模块 - FFmpeg集成
"""
import os
import subprocess
import json
import math
import tempfile
from pathlib import Path
from PIL import Image


class VideoProcessor:
    """视频处理器"""

    def __init__(self, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe'):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path
        # 在同目录下查找
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ['ffmpeg', 'ffmpeg.exe']:
            local_path = os.path.join(base_dir, name)
            if os.path.exists(local_path):
                self.ffmpeg = local_path
        for name in ['ffprobe', 'ffprobe.exe']:
            local_path = os.path.join(base_dir, name)
            if os.path.exists(local_path):
                self.ffprobe = local_path

    def get_video_info(self, video_path: str) -> dict:
        """获取视频信息"""
        try:
            cmd = [
                self.ffprobe, '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {}
            data = json.loads(result.stdout)
            info = {
                'duration': 0, 'width': 0, 'height': 0,
                'bitrate': 0, 'fps': 0, 'size': os.path.getsize(video_path)
            }
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    info['width'] = stream.get('width', 0)
                    info['height'] = stream.get('height', 0)
                    fps_str = stream.get('r_frame_rate', '0/1')
                    if '/' in fps_str:
                        a, b = fps_str.split('/')
                        info['fps'] = round(int(a) / max(int(b), 1), 2)
            fmt = data.get('format', {})
            info['duration'] = float(fmt.get('duration', 0))
            info['bitrate'] = int(fmt.get('bit_rate', 0))
            return info
        except Exception as e:
            return {}

    def format_duration(self, seconds: float) -> str:
        """格式化时长"""
        s = int(seconds)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h:
            return f'{h}:{m:02d}:{sec:02d}'
        return f'{m}:{sec:02d}'

    def clip_video(self, input_path: str, output_path: str,
                   start: float = 0, duration: float = 60,
                   resolution: str = '1920x1080', bitrate: str = '4M',
                   encoder: str = 'libx264',
                   progress_callback=None) -> bool:
        """裁剪视频"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            w, h = resolution.split('x')

            cmd = [
                self.ffmpeg, '-y',
                '-ss', str(start),
                '-i', input_path,
                '-t', str(duration),
                '-vf', f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', encoder,
                '-b:v', bitrate,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]

            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                universal_newlines=True
            )

            # 读取进度
            duration_info = None
            for line in process.stderr:
                if 'Duration:' in line and duration_info is None:
                    # 提取总时长
                    pass
                if 'time=' in line and progress_callback:
                    try:
                        time_str = line.split('time=')[1].split(' ')[0]
                        h, m, s = time_str.split(':')
                        current = int(h) * 3600 + int(m) * 60 + float(s)
                        pct = min(100, int(current / duration * 100))
                        progress_callback(pct)
                    except:
                        pass

            process.wait()
            return process.returncode == 0
        except Exception as e:
            return False

    def extract_screenshots(self, video_path: str, output_dir: str,
                            grid: str = '3x3', size: int = 1080,
                            output_filename: str = None) -> str:
        """提取视频截图并拼接成网格图"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            cols, rows = map(int, grid.split('x'))
            count = cols * rows

            info = self.get_video_info(video_path)
            duration = info.get('duration', 60)

            # 均匀提取截图
            interval = duration / (count + 1)
            screenshots = []
            tmp_dir = tempfile.mkdtemp()

            for i in range(count):
                ts = interval * (i + 1)
                out_file = os.path.join(tmp_dir, f'shot_{i:03d}.jpg')
                cmd = [
                    self.ffmpeg, '-y',
                    '-ss', str(ts),
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', '2',
                    out_file
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0 and os.path.exists(out_file):
                    screenshots.append(out_file)

            if not screenshots:
                return ''

            # 拼接成网格
            thumb_w = size // cols
            thumb_h = int(thumb_w * 9 / 16)

            grid_img = Image.new('RGB', (size, thumb_h * rows), (20, 20, 20))

            for idx, shot_path in enumerate(screenshots[:count]):
                try:
                    img = Image.open(shot_path)
                    img = img.resize((thumb_w, thumb_h), Image.LANCZOS)
                    row = idx // cols
                    col = idx % cols
                    grid_img.paste(img, (col * thumb_w, row * thumb_h))
                except:
                    pass

            if output_filename is None:
                base = os.path.splitext(os.path.basename(video_path))[0]
                output_filename = f'{base}_cover.jpg'

            out_path = os.path.join(output_dir, output_filename)
            grid_img.save(out_path, quality=85)

            # 清理临时文件
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

            return out_path
        except Exception as e:
            return ''

    def extract_thumbnail(self, video_path: str, output_path: str,
                          time_offset: float = 1.0) -> bool:
        """提取单帧缩略图"""
        try:
            cmd = [
                self.ffmpeg, '-y',
                '-ss', str(time_offset),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0
        except:
            return False

    def check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg, '-version'],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def batch_clip(self, input_files: list, output_dir: str,
                   start: float = 0, duration: float = 60,
                   resolution: str = '1920x1080', bitrate: str = '4M',
                   encoder: str = 'libx264',
                   progress_callback=None) -> list:
        """批量裁剪视频"""
        results = []
        for i, input_path in enumerate(input_files):
            base = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(output_dir, f'{base}_clipped.mp4')

            def pct_cb(pct):
                if progress_callback:
                    total_pct = int((i * 100 + pct) / len(input_files))
                    progress_callback(total_pct, i, input_path)

            success = self.clip_video(
                input_path, output_path, start, duration,
                resolution, bitrate, encoder, pct_cb
            )
            results.append({
                'input': input_path,
                'output': output_path if success else '',
                'success': success
            })
        return results
