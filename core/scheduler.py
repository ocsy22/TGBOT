"""
自动发布调度器
"""
import threading
import time
import json
import random
import os
from datetime import datetime, timedelta
from .database import DB
from .task_engine import TaskEngine


class AutoPublishScheduler:
    """自动发布调度器"""

    def __init__(self):
        self._running = False
        self._thread = None
        self._engine = TaskEngine()

    def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止调度器"""
        self._running = False

    def _loop(self):
        """主循环"""
        while self._running:
            try:
                self._check_rules()
            except Exception as e:
                pass
            time.sleep(30)  # 每30秒检查一次

    def _check_rules(self):
        """检查是否有需要执行的规则"""
        rules = DB.fetchall('SELECT * FROM auto_publish_rules WHERE enabled=1')
        now = datetime.now()

        for rule in rules:
            if self._should_execute(rule, now):
                self._execute_rule(rule)

    def _should_execute(self, rule: dict, now: datetime) -> bool:
        """判断是否应该执行规则"""
        schedule_type = rule.get('schedule_type', 'daily')
        schedule_time = rule.get('schedule_time', '20:55')
        last_publish = rule.get('last_publish', '')

        try:
            target_hour, target_min = map(int, schedule_time.split(':'))
        except:
            return False

        # 检查是否在执行时间
        if now.hour != target_hour or now.minute != target_min:
            return False

        # 检查今天是否已经执行过
        if last_publish:
            try:
                last_dt = datetime.strptime(last_publish, '%Y-%m-%d %H:%M:%S')
                if last_dt.date() == now.date() and schedule_type == 'daily':
                    return False
            except:
                pass

        return True

    def _execute_rule(self, rule: dict):
        """执行自动发布规则"""
        channel_ids = json.loads(rule.get('channel_ids', '[]'))
        folder_id = rule.get('media_folder_id', 0)

        if not channel_ids or not folder_id:
            return

        # 获取未发布的素材
        files = DB.fetchall('SELECT * FROM media_files WHERE folder_id=?', (folder_id,))
        if not files:
            return

        # 随机或顺序选择
        if rule.get('random_order'):
            random.shuffle(files)

        # 选择一个未发布的文件
        selected = files[0] if files else None
        if not selected:
            return

        # 创建并执行任务
        task_id = DB.execute(
            '''INSERT INTO tasks (title, channel_ids, media_file_id, 
               copy_template_id, writing_direction_id, ai_generate, status)
               VALUES (?,?,?,?,?,?,?)''',
            (
                rule['name'],
                json.dumps(channel_ids),
                selected['id'],
                rule.get('copy_template_id', 0),
                rule.get('writing_direction_id', 0),
                1,
                'pending'
            )
        )

        # 更新最后发布时间
        DB.execute(
            "UPDATE auto_publish_rules SET last_publish=?, published_count=published_count+1 WHERE id=?",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rule['id'])
        )

        # 异步执行
        self._engine.execute_task_async(task_id)


# 全局调度器实例
_scheduler = None


def get_scheduler() -> AutoPublishScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AutoPublishScheduler()
    return _scheduler
