# 小米手表和手机壁纸个性化

`photo-wallpaper` 是一个通用的 Codex Skill，把自己的照片做成适合目标屏幕的静态壁纸或动态轮播。它适用于不同品牌的手机，可按屏幕比例裁切照片，并在设计锁屏时为系统时钟、通知和指纹区域留出空间。

## 主要功能

- **静态壁纸**。用一张照片导出指定尺寸的 JPG 或 PNG。脚本按 EXIF 方向校正照片、等比裁切，并可调整裁切位置。
- **动态轮播**。按传入顺序导出 30 fps 的静音 H.264 MP4，可设置每张的播放时长和交叉淡化时长，最后一张会淡化回首张。手机能否将 MP4 设为锁屏壁纸取决于系统提供的入口。
- **预览与设备扩展**。Skill 提供锁屏构图、现有 HTML 预览转视频和小米表盘的工作流程。HTML 导出依赖浏览器。原生表盘还需要匹配机型的工程、编译工具和导入方式。[小米表盘参考](photo-wallpaper/references/xiaomi-watchfaces.md)

## 安装方法

1. 获取项目文件，将整个 `photo-wallpaper` 文件夹复制到目标项目的 `.agents/skills/`。也可以复制到用户目录的 `~/.agents/skills/`，供多个项目使用。安装后的技能入口应为 `photo-wallpaper/SKILL.md`。[Codex 技能目录](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
2. 如果要使用附带的导出脚本，准备 Python 3.8 或更新版本并安装 Pillow 9.1 或更新版本。可以跳过 Skill 安装，直接运行脚本。

   ```sh
   python -m pip install "Pillow>=9.1"
   ```

3. 导出 MP4 还需安装带 `libx264` 编码器的 FFmpeg。将它加入 `PATH`，或运行时用 `--ffmpeg` 指定可执行文件。

## 使用方法

在 Codex 中选择 `photo-wallpaper`，提供本地照片、目标机型或像素尺寸，以及所需的输出格式。制作锁屏预览时，可以同时提供锁屏截图来核对系统控件的位置。

> 用我提供的三张照片做一段 1080×2400 的锁屏轮播，按文件名顺序播放。每张占 3 秒，包含 0.6 秒交叉淡化。请给我带时钟占位的预览，以及单独的 MP4 壁纸。

直接运行脚本时，在项目根目录执行以下示例。`--size` 使用 `宽x高`，`--output` 的扩展名决定输出格式，`--center X Y` 可用两个 0 到 1 之间的数调整裁切位置。脚本对所有输入使用同一组裁切参数，并拒绝覆盖现有文件。

## 输入输出示例

示例中的文件名是占位符，请替换为自己的照片。

### 单张照片 → JPG 壁纸

```sh
python photo-wallpaper/scripts/render_wallpaper.py --size 1080x2400 --output lockscreen.jpg photo-01.jpg
```

输入 `photo-01.jpg`，输出 `1080×2400` 的 `lockscreen.jpg`。也可以把输出扩展名改为 `.png`。

### 三张照片 → MP4 轮播

```sh
python photo-wallpaper/scripts/render_wallpaper.py --size 1080x2400 --output lockscreen.mp4 --seconds 3 --fade 0.6 photo-01.jpg photo-02.jpg photo-03.jpg
```

依次输入三张照片，输出约 9 秒的 `1080×2400` 静音视频。`--seconds` 包含淡化时间，`--fade 0` 使用直接切换。MP4 的宽和高都需为偶数。

## 许可

公开内容为技能文档与通用代码，采用 [MIT License](LICENSE)。输入照片、预览和导出文件在本地处理。
