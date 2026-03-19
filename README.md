# TG Auto Publisher

**Telegram 频道自动化运营工具** - 一键实现视频裁剪、AI文案生成、定时发布到多频道

## 功能特性

### 核心功能
- ✅ **多账号/多频道管理** - Bot API + MTProto 真实账号，同时发布到多个频道
- ✅ **AI 自动写作文案** - 支持 12 家 AI 服务商，含成人内容支持
- ✅ **视频 FFmpeg 处理** - 自动裁剪、截图网格封面、批量处理
- ✅ **定时自动发布** - 每日固定时间自动发布，随机顺序
- ✅ **素材库管理** - 文件夹方式管理视频/图片/音频
- ✅ **大文件支持** - MTProto 协议发送最大 2GB 视频

### AI 支持的服务商 (含无内容限制)
| 服务商 | 特点 |
|--------|------|
| 🔑 Grok (xAI) | 无内容限制，支持成人内容 |
| 🔑 Together AI | 开源模型，无审查 |
| 🔑 Mistral | 欧洲模型，无内容限制 |
| 🔑 DeepSeek | 中文优化，便宜 |
| 🔑 Groq | 超高速推理 |
| 🔑 Gemini | 免费额度 |
| 🔑 SambaNova | 免费高速 |
| 🔑 OpenAI | GPT-4系列 |

## 下载

前往 [Releases](https://github.com/ocsy22/TGBOT/releases) 下载最新版本。

### Windows 用户
1. 从 Releases 下载 `TGAutoPublisher_windows_x64.exe`（需要在 Windows 机器上编译）
2. 将 `ffmpeg.exe` 放在程序同目录
3. 双击运行

### 从源码运行
```bash
pip install -r requirements.txt
python main.py
```

## FFmpeg 配置

程序使用 FFmpeg 进行视频处理。**FFmpeg 放置位置：**
- 将 `ffmpeg.exe` (Windows) 或 `ffmpeg` (Linux/Mac) 放在程序**同目录**下
- 或将 ffmpeg 加入系统 PATH
- 或在 **设置 → 视频处理** 中填写完整路径

下载地址：https://ffmpeg.org/download.html

## 快速开始

1. **配置 Telegram API**
   - 前往 https://my.telegram.org 获取 API ID 和 Hash
   - 在 **设置 → 频道管理** 中添加 API 配置

2. **添加 Bot 或账号**
   - Bot: 前往 @BotFather 创建 Bot 获取 Token
   - 账号: 使用真实手机号通过 MTProto 登录（支持大文件）

3. **添加频道**
   - 将 Bot 设为频道管理员
   - 在频道管理中添加频道信息（用户名或 Chat ID）

4. **上传素材**
   - 在素材库中添加视频文件夹
   - 支持 mp4/avi/mov/mkv 等格式

5. **配置 AI**
   - 在设置中选择 AI 服务商并填写 API Key
   - 推荐使用 Grok 或 Together AI（无内容限制）

6. **创建任务/设置自动发布**
   - 任务中心：一次性任务（选择视频 → 裁剪 → AI文案 → 发布）
   - 自动发布：定时规则（每天 X 时自动从素材库选视频发布）

## 目录结构

```
tg_publisher/
├── main.py              # 程序入口
├── core/
│   ├── database.py      # SQLite数据库
│   ├── ai_generator.py  # AI文案生成
│   ├── video_processor.py # 视频处理 (FFmpeg)
│   ├── telegram_sender.py # TG发送 (Bot+MTProto)
│   ├── task_engine.py   # 任务执行引擎
│   └── scheduler.py     # 自动发布调度器
├── ui/
│   ├── main_window.py   # 主窗口
│   ├── styles.py        # UI样式
│   └── pages/           # 各功能页面
├── data/                # 数据存储 (SQLite)
├── requirements.txt
└── build.py             # 打包脚本
```

## 编译 Windows EXE

在 Windows 机器上执行：
```bash
pip install -r requirements.txt
python build.py
```
生成的 EXE 在 `dist/TGAutoPublisher.exe`

## 注意事项

- 首次运行 MTProto 账号时需要输入短信验证码
- 使用 Bot 发送大于 50MB 的文件需要配置本地 Bot API 或使用 MTProto 账号
- 建议使用代理访问 Telegram（国内环境）

## License

MIT License
