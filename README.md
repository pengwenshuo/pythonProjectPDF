# PDFgj

一款 Windows 平台的 Python 命令行工具，用于图片/Word/Excel/PPT 转 PDF 以及 PDF 合并。

## 功能特性

- **图片转 PDF** — 支持 JPG、PNG、WebP、BMP、GIF、TIFF 等格式，自动处理透明背景，支持灰度模式
- **Word 转 PDF** — 通过 COM 自动化批量转换 .docx/.doc，仅启动一次 Word
- **Excel 转 PDF** — 通过 COM 自动化批量转换 .xlsx/.xls/.xlsm，自动重算公式
- **PPT 转 PDF** — 通过 COM 自动化批量转换 .pptx/.ppt，支持指定页码范围导出
- **PDF 合并** — 流式合并目录下多个 PDF，支持按名称/时间排序
- **递归扫描** — 所有模式均支持递归处理子目录
- **覆盖保护** — 同名文件存在时提示确认，支持 `-y` 跳过确认

## 系统要求

- Windows 7+（Word/Excel/PPT 转换需要安装对应的 Office 组件）
- Python 3.9+

## 安装

```bash
# 克隆仓库
git clone https://github.com/pengwenshuo/pythonProjectPDF.git
cd pythonProjectPDF

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate

# 安装（开发模式）
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 图片转 PDF（默认模式）
pdfgj                    # 当前目录所有图片
pdfgj -g                 # 灰度模式
pdfgj -r                 # 递归子目录

# Word 转 PDF
pdfgj -w                 # 当前目录所有 Word 文档
pdfgj -wr                # 递归子目录

# Excel 转 PDF
pdfgj -e                 # 当前目录所有 Excel 表格
pdfgj -er                # 递归子目录

# PPT 转 PDF
pdfgj -p                 # 当前目录所有 PPT
pdfgj -pr                # 递归子目录
pdfgj -p --slides 1,3,5-8  # 指定页码范围

# PDF 合并
pdfgj -m                 # 合并为 merged.pdf
pdfgj -m -o output.pdf   # 指定输出文件名
pdfgj -m --sortby mtime  # 按修改时间排序
```

### Python 模块调用

```bash
python -m pdfgj -w       # Word → PDF
python -m pdfgj -m       # 合并 PDF
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
| `-p`, `--ppt` | PPT 模式：PowerPoint 演示文稿转 PDF |
| `--slides` | PPT 模式：指定导出页码，如 "1,3,5-8" |
| `-o`, `--output` | 合并模式：指定输出文件名（默认 merged.pdf） |
| `-r`, `--recursive` | 递归查找子目录 |
| `--sortby` | 合并排序依据（name / ctime / mtime） |
| `-y`, `--yes` | 跳过所有覆盖确认 |
| `--kill-office` | 允许按进程名终止 Office 进程 |

## 支持的文件格式

| 类型 | 格式 |
|------|------|
| 图片 | .jpg .jpeg .png .webp .bmp .gif .tiff .tif |
| Word | .docx .doc |
| Excel | .xlsx .xls .xlsm |
| PPT | .pptx .ppt |

## 项目结构

```
├── pyproject.toml            # 打包配置与依赖声明
├── runPDF.bat                # 快捷运行脚本
├── pdfgj/                    # 核心模块包
│   ├── cli.py                # 命令行参数解析与主流程
│   ├── image_convert.py      # 图片转 PDF
│   ├── word_convert.py       # Word 转 PDF（COM）
│   ├── excel_convert.py      # Excel 转 PDF（COM）
│   ├── ppt_convert.py        # PPT 转 PDF（COM）
│   ├── merge.py              # PDF 合并
│   ├── com_core.py           # COM 公共层（进程管理/错误分类）
│   ├── constants.py          # 文件格式常量与 COM 常量
│   ├── deps.py               # 依赖检测
│   └── utils.py              # 工具函数（排序/进度条/覆盖保护）
└── tests/                    # 单元测试
    ├── test_utils.py         # utils 模块测试
    └── test_com_core.py      # com_core 模块测试
```

## 开发

### 运行测试

```bash
# 安装测试依赖
pip install -e ".[test]"

# 运行测试
pytest tests/ -v
```

### 语法检查

```bash
python -m py_compile pdfgj/*.py
```

## 注意事项

- Word/Excel/PPT 转换功能仅在 Windows 平台可用，且需要安装对应的 Office 组件
- 图片转 PDF 和 PDF 合成功能是跨平台的
- 转换过程中会启动 Office 应用，转换完成后会自动关闭
- 使用 `--kill-office` 参数时请确保没有其他未保存的 Office 文档

## 许可证

MIT License
