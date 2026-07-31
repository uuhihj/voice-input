# 🎤 Voice Input

> Alt + Numpad+ → 录音 → AI 语音识别 → 文字直接输入到光标位置

系统托盘运行，无窗口，中英混合识别，PySide6 毛玻璃设置面板。

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
# ModelScope（国内快）
pip install modelscope
modelscope download --model keepitsimple/faster-whisper-large-v3 --local_dir ./models

# 或 HuggingFace
huggingface-cli download keepitsimple/faster-whisper-large-v3 --local-dir ./models
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行

```bash
python voice_input.py
```

托盘出现绿色图标即就绪。也可以双击 `voice_input_launcher.bat` 或 `voice_input_launcher.vbs`（静默启动）。

---

## 快捷键

| 操作 | 默认快捷键 |
|------|-----------|
| 开始/停止录音 | `Alt` + `Numpad +` |
| 退出程序 | `Alt` + `Numpad -` |
| 打开设置 | 右键托盘图标 → ⚙️ 设置 |

录音时屏幕顶部/底部会出现彩色指示条。设置窗口中可以自定义快捷键、模型参数和外观样式。

---

## 项目结构

```
voice_input.py                    主程序
voice_input_config.py             配置管理
voice_input_settings_pyside.py    设置窗口（PySide6 毛玻璃）
voice_input_indicator.py          浮动录音指示器
voice_input_config.json           配置文件（自动生成）
voice_input.spec                  PyInstaller 打包配置
voice_input_launcher.bat          启动脚本（控制台）
voice_input_launcher.vbs          启动脚本（静默）
requirements.txt                  依赖清单
models/                           语音模型（需自行下载）
```

---

## 打包为 EXE

```bash
pip install pyinstaller
pyinstaller voice_input.spec
```

产物在 `dist/VoiceInput.exe`。把 `models/` 文件夹放在 exe 同目录即可运行。

---

## 技术栈

- 语音识别：[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (large-v3, CUDA)
- 音频采集：sounddevice (PortAudio)
- 全局热键：keyboard
- 系统托盘：pystray + Pillow
- GUI 设置：PySide6 + Windows DWM 亚克力毛玻璃
- 浮动指示器：tkinter

---

## 常见问题

**Q: 提示 "Model not found"？**
A: 模型还没下载或路径不对。按上面步骤下载模型到 `models/` 目录。

**Q: 提示 "Cannot load model"？**
A: 显卡驱动或 CUDA 有问题，在设置中切换到 CPU 模式试试。

**Q: 托盘图标看不到？**
A: Windows 会自动隐藏图标，点击任务栏 `^` 展开。

**Q: 输出是繁体字？**
A: 已内置 `zhconv` 自动转简体。

---

## License

MIT
