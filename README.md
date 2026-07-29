# 🎤 Voice Input

> Alt + 小键盘加号 → 录音 → AI 语音识别 → 文字直接输入到光标位置

系统托盘运行，无窗口，中英混合识别，樱花粉设置面板。

---

## 系统要求

- Windows 10/11 64 位
- NVIDIA 显卡（RTX 20 系列及以上，6GB+ 显存）
- 麦克风
- Python 3.12+

---

## 快速开始

### 1. 下载模型

```bash
# 方式一：ModelScope（推荐，国内快）
pip install modelscope
modelscope download --model keepitsimple/faster-whisper-large-v3 --local_dir ./models

# 方式二：HuggingFace（需要代理）
huggingface-cli download keepitsimple/faster-whisper-large-v3 --local-dir ./models
```

### 2. 安装依赖

```bash
pip install faster-whisper sounddevice keyboard pystray Pillow zhconv numpy
# CUDA 加速（需要 RTX 显卡）
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-runtime-cu12
```

### 3. 运行

```bash
python voice_input.py
```

托盘出现绿色图标即就绪。

---

## 快捷键

| 操作 | 默认快捷键 |
|------|-----------|
| 开始/停止录音 | `Alt` + `Numpad +` |
| 退出程序 | `Alt` + `Numpad -` |
| 打开设置 | 右键托盘图标 → 设置 |

录音时屏幕顶部会出现红色指示条。

---

## 打包为 EXE

```bash
pip install pyinstaller
pyinstaller voice_input.spec
```

产物在 `dist/VoiceInput.exe`。把 `models/` 文件夹放在 exe 同目录下即可。

---

## 项目结构

```
voice_input.py          # 主程序：托盘、热键、录音、转录
voice_input_config.py   # 配置管理（JSON 读写、默认值）
voice_input_settings.py # 设置窗口 GUI（樱花主题）
voice_input_indicator.py # 浮动录音指示器
voice_input.spec        # PyInstaller 配置
models/                 # 语音模型（需自行下载）
```

---

## 技术栈

- 语音识别：[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (large-v3, CUDA)
- 音频采集：sounddevice (PortAudio)
- 全局热键：keyboard
- 系统托盘：pystray + Pillow
- GUI：tkinter

---

## 常见问题

**Q: 双击没反应？**
A: 检查 `models/` 文件夹是否存在且完整。

**Q: 提示 "Cannot load model"？**
A: 检查显卡驱动和 CUDA 是否正常，或在设置中切换到 CPU 模式。

**Q: 托盘图标看不到？**
A: Windows 会自动隐藏不常用的图标，点击任务栏 `^` 展开。

**Q: 输出是繁体字？**
A: 已内置 `zhconv` 自动转简体。如还有问题请提 issue。

---

## License

MIT
