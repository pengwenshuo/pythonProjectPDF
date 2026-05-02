# PDFgj — 图片 / Word / Excel 转 PDF 与 PDF 合并工具

一款 Windows 平台 Python 命令行工具，可将图片、Word 文档、Excel 表格批量转换为 PDF，并支持 PDF 合并。

## 功能

- **图片转 PDF** — 支持 JPG、PNG、WebP、BMP、GIF、TIFF 等常见格式，自动处理透明背景（白底填充），支持灰度模式
- **Word 转 PDF** — 通过 Word COM 对象批量转换 .docx / .doc，仅启动一次 Word，支持进度显示
- **Excel 转 PDF** — 通过 Excel COM 对象批量转换 .xlsx / .xls / .xlsm，自动重算公式，仅启动一次 Excel
- **PDF 合并** — 流式合并目录下多个 PDF，支持按名称/创建时间/修改时间排序
- **递归扫描** — 所有模式均支持 `-r` 递归处理子目录
- **覆盖保护** — 同名 PDF 存在时提示确认，支持 `-y` 跳过确认（批量自动化）
- **COM 进程管理** — 转换完成后安全退出 Office 进程，异常时按 PID 精确终止

## 系统要求

- Windows 7+（Word/Excel 转 PDF 需要安装对应的 Office 组件）
- Python 3.9+

## 安装

```bash
# 1. 克隆或下载项目
# 2. 安装依赖
pip install -r requirements.txt
```

依赖: pillow, PyPDF2 (或 pypdf), pywin32

## 使用方式

### 快捷命令（推荐）

项目附带了批处理脚本 `runPDF.bat`，可在当前目录直接使用：

```bash
runPDF -w            # Word → PDF
runPDF -e            # Excel → PDF
runPDF -m            # 合并 PDF
runPDF -gr           # 图片→PDF(灰度+递归)
runPDF -mro 合集.pdf # 合并+递归+指定输出
```

### 完整命令

```bash
# 图片转 PDF（默认模式，彩色）
python PDFgj.py

# 图片转 PDF（灰度 + 递归子目录）
python PDFgj.py -gr

# Word 文档转 PDF
python PDFgj.py -w

# Word 文档转 PDF（递归子目录）
python PDFgj.py -wr

# Excel 表格转 PDF
python PDFgj.py -e

# Excel 表格转 PDF（递归子目录）
python PDFgj.py -er

# 合并当前目录下所有 PDF
python PDFgj.py -m

# 合并 PDF，指定输出文件名并递归
python PDFgj.py -mro output.pdf

# 跳过所有覆盖确认
python PDFgj.py -w -y

# 按修改时间排序合并
python PDFgj.py -m --sortby mtime
```

### Python 模块调用

```bash
python -m pdfgj -w    # Word → PDF（新入口）
python -m pdfgj -m    # 合并 PDF（新入口）
```

### 作为库使用

```python
from pdfgj import image_to_pdf, merge_pdfs

# 单张图片转 PDF
image_to_pdf("photo.jpg")

# 合并目录下所有 PDF
merge_pdfs(".")
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-m`, `--merge` | 合并模式：合并目录下所有 PDF |
| `-g`, `--gray` | 灰度模式：图片转灰度 PDF |
| `-w`, `--word` | Word 模式：Word 文档转 PDF |
| `-e`, `--excel` | Excel 模式：Excel 表格转 PDF |
| `-o`, `--output` | 合并模式：指定输出文件名（默认 merged.pdf） |
| `-r`, `--recursive` | 递归查找子目录（适用于所有模式） |
| `--sortby` | 合并排序依据（name / ctime / mtime，默认 name） |
| `-y`, `--yes` | 跳过所有覆盖确认 |
| `--kill-office` | 允许按进程名终止 Office 进程 |

## 支持的文件格式

| 类型 | 格式 |
|------|------|
| 图片 | .jpg .jpeg .png .webp .bmp .gif .tiff .tif |
| Word | .docx .doc |
| Excel | .xlsx .xls .xlsm |

## 项目结构

```
├── PDFgj.py              # 单文件入口（兼容旧习惯）
├── pdfgj/                # 核心模块包
│   ├── cli.py            # 命令行参数解析与主流程
│   ├── image_convert.py  # 图片转 PDF
│   ├── word_convert.py   # Word 转 PDF（COM）
│   ├── excel_convert.py  # Excel 转 PDF（COM）
│   ├── merge.py          # PDF 合并
│   ├── com_core.py       # COM 公共层（进程管理/错误分类）
│   ├── constants.py      # 文件格式常量与 COM 常量
│   ├── deps.py           # 依赖检测（pypdf / win32com）
│   └── utils.py          # 工具函数（排序/进度条/覆盖保护）
├── runPDF.bat            # 快捷运行脚本
└── requirements.txt      # Python 依赖
```
