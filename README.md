# 🎤 衔音令

按下快捷键 → 说话 → 文字自动输入到电脑上。

---

## 📥 下载和安装（跟着做就行）

### 第一步：安装 Python

1. 打开 https://www.python.org/downloads/
2. 点黄色的大按钮下载
3. 打开下载的文件
4. ⚠️ **一定要勾选底部的 "Add Python to PATH"**（这步很重要！）
5. 点 "Install Now"

### 第二步：下载本项目

点右上角绿色的 **Code** 按钮 → **Download ZIP**，下载后解压到任意文件夹。

### 第三步：安装

**双击解压出来的 `install.bat`**，等待完成（约 10-30 分钟，取决于网速）。

### 第四步：启动

**双击 `voice_input_launcher.bat`**，右下角出现绿色圆点图标就成功了。

---

## ⌨️ 怎么用

| 你想做什么 | 怎么操作 |
|-----------|---------|
| 开始说话 | 按 `Alt` + `小键盘加号`（最右边的 `+`） |
| 说完停止 | 再按一次 `Alt` + `小键盘加号` |
| 关闭程序 | 按 `Alt` + `小键盘减号` |
| 改设置 | 右键右下角绿色图标 → 设置 |

说话时会弹出一个彩色条，代表正在录音。

---

## ❓ 遇到问题？

| 问题 | 解决 |
|------|------|
| 双击没反应 | Python 没装好，重做第一步，记得勾选 Add to PATH |
| 提示找不到模型 | 重新双击 `install.bat` |
| 按快捷键没用 | 确认按的是键盘最右边的小键盘 + 号，不是字母上面的 |
| 图标不见了 | 点任务栏右下角的 `^` 箭头，图标在里面 |
| 识别出繁体字 | 会自动转简体，不影响使用 |

---

## 📁 文件说明

```
install.bat                      一键安装（双击这个开始）
voice_input_launcher.bat         启动程序（双击运行）
voice_input.py                   主程序
voice_input_config.py            配置
voice_input_settings_pyside.py   设置窗口
voice_input_indicator.py         录音提示条
requirements.txt                 依赖列表
```

---

## 🛠 技术信息

- 语音识别：faster-whisper large-v3（CUDA）
- 需要 NVIDIA 显卡（GTX 20 系列以上）
- 支持中英文混合识别
- 设置窗口使用 Windows 毛玻璃效果
