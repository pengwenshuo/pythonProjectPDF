# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PDFgj 是一个 Windows 平台的 Python 命令行工具，用于图片/Word/Excel 转 PDF 以及 PDF 合并。仅支持 Windows（Word/Excel 转换依赖 Office COM 自动化）。

## 常用命令

```bash
# 安装（开发模式，改代码即时生效）
pip install -e .

# 运行工具
runPDF [args]              # 快捷脚本（任意目录，需项目目录在 PATH）
python -m pdfgj [args]     # 模块入口
pdfgj [args]               # 安装后可用（需先激活虚拟环境）

# 语法检查（无自动化测试，用此验证代码正确性）
python -m py_compile pdfgj/*.py

# 查看帮助
pdfgj -h
```

## 架构

模块间遵循严格的自底向上依赖层次，无循环导入：

```
constants.py          (零依赖 — 文件格式集合 + COM 枚举常量)
      ↓
    deps.py           (pypdf + win32com 依赖检测，三级回退)
      ↓
    utils.py          (排序、文件列表、进度条、覆盖保护、全局标志)
      ↓
   com_core.py        (COM 进程生命周期、HRESULT 错误分类、批量转换编排)
      ↓
   ┌──┼──┐
image word excel      (转换器模块：各自通过 com_core 调用 COM，通过 utils 获取辅助函数)
   └──┼──┘
      ↓
   merge.py           (通过 pypdf 流式合并 PDF)
      ↓
   cli.py             (argparse 解析参数 + main() 编排所有流程)
```

**五种互斥模式**（通过 argparse 互斥组实现，默认为合并）：
- **PDF 合并**（默认/`-m`）：`merge.py`，使用 pypdf `PdfWriter`
- **图片转 PDF**（`-i`）：`image_convert.py`，使用 Pillow，自动处理 RGBA/P→RGB
- **Word 转 PDF**（`-w`）：`word_convert.py`，COM 自动化 `Word.Application`
- **Excel 转 PDF**（`-e`）：`excel_convert.py`，COM 自动化 `Excel.Application`
- **PPT 转 PDF**（`-p`）：`ppt_convert.py`，COM 自动化 `PowerPoint.Application`

**关键设计要点**：
- `WordConverter` / `ExcelConverter` 是上下文管理器，`com_core._batch_convert()` 只启动一次 Office 应用，循环调用 `.convert()`，避免重复启动开销
- COM 进程三级终止策略：`app.Quit()` → `taskkill /F /PID` → `taskkill /F /IM`（仅 `--kill-office` 时）
- `utils.py` 中的 `_force_overwrite` 和 `_allow_kill_office` 是模块级全局标志，由 `cli.py` 在参数解析后设置
- `deps.py` 对 PDF 库有三级回退：`pypdf` → `PyPDF2 >= 2.0` → `PyPDF2 < 2.0`
- `pywin32` 是延迟导入的，未安装 Office 的用户仍可使用图片转 PDF 和合并功能

## 注意事项

- 项目无自动化测试，修改后需手动验证
- 所有文档和用户界面使用简体中文
