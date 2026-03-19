"""
视频处理模块 - 使用FFmpeg进行视频裁剪和截图
"""
import os
import subprocess
import shutil
from pathlib import Path


class VideoProcessor:
    """视频处理器"""

    def __init__(self, ffmpeg_path: str = ''):
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        """自动查找FFmpeg"""
        import sys
        # 检查系统PATH
        found = shutil.which('ffmpeg')
        if found:
            return found
        # 检查程序同目录
        exe_dir = os.path.dirname(sys.executable)
        for name in ['ffmpeg.exe', 'ffmpeg']:
            p = os.path.join(exe_dir, name)
            if os.path.exists(p):
                return p
        return 'ffmpeg'

    def _get_output_dir(self, input_file: str, folder_name: str = '已裁剪') -> str:
        """获取输出目录（在原文件同级创建文件夹）"""
        parent_dir = os.path.dirname(os.path.abspath(input_file))
        out_dir = os.path.join(parent_dir, folder_name)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _get_video_duration(self, input_file: str) -> float:
        """获取视频时长（秒）"""
        try:
            cmd = [
                self.ffmpeg_path, '-i', input_file,
                '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1'
            ]
            # 用ffprobe更准确，但ffmpeg也能获取
            probe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            if os.path.exists(probe_path):
                cmd[0] = probe_path

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and line.replace('.', '').isdigit():
                    return float(line)
        except Exception:
            pass
        return 0.0

    def crop_video(self, input_file: str, folder_name: str = '已裁剪',
                   start_time: str = '00:00:00', end_time: str = '',
                   duration_sec: int = 0) -> str:
        """
        裁剪视频片段
        :param input_file: 输入视频路径
        :param folder_name: 输出文件夹名（在原文件同目录）
        :param start_time: 起始时间 HH:MM:SS
        :param end_time: 结束时间 HH:MM:SS（优先）
        :param duration_sec: 持续秒数（end_time为空时使用）
        :return: 输出文件路径
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件不存在: {input_file}")

        out_dir = self._get_output_dir(input_file, folder_name)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        ext = os.path.splitext(input_file)[1] or '.mp4'
        out_file = os.path.join(out_dir, f"{base_name}_裁剪{ext}")

        cmd = [self.ffmpeg_path, '-y', '-i', input_file]

        if start_time and start_time != '00:00:00':
            cmd += ['-ss', start_time]

        if end_time:
            cmd += ['-to', end_time]
        elif duration_sec > 0:
            cmd += ['-t', str(duration_sec)]

        cmd += [
            '-c', 'copy',  # 无损复制，速度快
            '-avoid_negative_ts', 'make_zero',
            out_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # 如果copy失败，尝试重新编码
            cmd_re = [self.ffmpeg_path, '-y', '-i', input_file]
            if start_time and start_time != '00:00:00':
                cmd_re += ['-ss', start_time]
            if end_time:
                cmd_re += ['-to', end_time]
            elif duration_sec > 0:
                cmd_re += ['-t', str(duration_sec)]
            cmd_re += ['-c:v', 'libx264', '-c:a', 'aac', '-crf', '23', out_file]
            result2 = subprocess.run(cmd_re, capture_output=True, text=True, timeout=600)
            if result2.returncode != 0:
                raise RuntimeError(f"裁剪失败: {result2.stderr[-500:]}")

        return out_file if os.path.exists(out_file) else ''

    def capture_screenshots(self, input_file: str, folder_name: str = '已裁剪',
                            grid: str = '3x3', count: int = 9) -> list:
        """
        从视频均匀截取多张截图
        :param input_file: 输入视频路径
        :param folder_name: 输出文件夹名
        :param grid: 网格规格（如3x3）
        :param count: 截图数量
        :return: 截图路径列表
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件不存在: {input_file}")

        # 获取视频时长
        duration = self._get_video_duration(input_file)
        if duration <= 0:
            # 尝试用ffmpeg直接获取
            duration = 60.0  # 默认60秒

        out_dir = self._get_output_dir(input_file, folder_name)
        base_name = os.path.splitext(os.path.basename(input_file))[0]

        screenshots = []
        interval = duration / (count + 1)

        for i in range(count):
            timestamp = interval * (i + 1)
            out_file = os.path.join(out_dir, f"{base_name}_截图_{i + 1:02d}.jpg")

            cmd = [
                self.ffmpeg_path, '-y',
                '-ss', str(timestamp),
                '-i', input_file,
                '-vframes', '1',
                '-q:v', '2',
                '-vf', 'scale=1280:-1',
                out_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(out_file):
                screenshots.append(out_file)

        return screenshots

    def create_thumbnail_grid(self, screenshots: list, output_path: str,
                               cols: int = 3) -> str:
        """将多张截图合并为网格缩略图"""
        try:
            from PIL import Image
            rows = (len(screenshots) + cols - 1) // cols
            if not screenshots:
                return ''

            # 读取第一张确定尺寸
            first = Image.open(screenshots[0])
            w, h = first.size
            thumb_w, thumb_h = min(w, 426), min(h, 240)

            grid_img = Image.new('RGB', (thumb_w * cols, thumb_h * rows), (20, 20, 20))

            for idx, ss_path in enumerate(screenshots):
                try:
                    img = Image.open(ss_path)
                    img = img.resize((thumb_w, thumb_h), Image.LANCZOS)
                    row, col = divmod(idx, cols)
                    grid_img.paste(img, (col * thumb_w, row * thumb_h))
                except Exception:
                    pass

            grid_img.save(output_path, 'JPEG', quality=85)
            return output_path
        except Exception:
            return ''
