# CLI 默认模式重构 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PDF 合并设为默认模式，图片转 PDF 改用 `-i` 参数，去掉灰度功能。

**Architecture:** 最小改动方案 — 只修改 argparse 定义、main() 分支逻辑和 image_convert.py 的灰度参数。不涉及模块拆分或架构调整。

**Tech Stack:** Python 3.9+, argparse, Pillow, pypdf

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `pdfgj/cli.py` | 修改 | argparse 参数定义 + main() 分支逻辑 |
| `pdfgj/image_convert.py` | 修改 | 去掉 `grayscale` 参数 |
| `CLAUDE.md` | 修改 | 更新模式描述 |
| `pyproject.toml` | 无需修改 | 描述已涵盖所有模式 |

---

### Task 1: 修改 image_convert.py — 去掉灰度参数

**Files:**
- Modify: `pdfgj/image_convert.py`

- [ ] **Step 1: 去掉 grayscale 参数和灰度转换逻辑**

将 `image_to_pdf` 函数签名中的 `grayscale: bool = False` 参数删除，同时删除函数体中的灰度转换代码块（第 25-26 行）。

修改后的完整文件内容：

```python
"""图片转 PDF"""

from pathlib import Path
from PIL import Image

from .utils import _check_overwrite


def image_to_pdf(image_path: Path) -> bool:
    """单张图片转 PDF，自动将透明背景转为白底"""
    pdf_path = image_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False
    try:
        img = Image.open(image_path)
        # 透明/调色板模式统一转 RGB，透明部分用白底填充
        if img.mode in ('RGBA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(pdf_path, format="PDF", save_all=True, resolution=200.0)
        print(f"  [OK] {image_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        print(f"  [失败] {image_path.name}: {err}")
        return False
```

- [ ] **Step 2: 语法检查**

Run: `python -m py_compile pdfgj/image_convert.py`
Expected: 无输出（编译成功）

---

### Task 2: 修改 cli.py — argparse 参数重定义

**Files:**
- Modify: `pdfgj/cli.py:18-75` (parse_args 函数)

- [ ] **Step 1: 替换互斥组中的 -g 为 -i**

将 `cli.py` 第 45 行：
```python
mode.add_argument('-g', '--gray', action='store_true', help='灰度模式：图片转灰度 PDF')
```
替换为：
```python
mode.add_argument('-i', '--image', action='store_true', help='图片模式：图片转 PDF')
```

- [ ] **Step 2: 更新 epilog 中的快捷方式示例**

将 `cli.py` 第 22-39 行的 epilog 字符串替换为：

```python
        epilog='''
快捷方式（任意终端直接输入）:
  runPDF                       合并PDF(默认)
  runPDF -i                    图片→PDF
  runPDF -w                   Word→PDF
  runPDF -e                   Excel→PDF
  runPDF -p                   PPT→PDF
  runPDF -ro 合集.pdf         合并+递归+指定输出

完整命令:
  python PDFgj.py              合并PDF(默认)       python PDFgj.py -i          图片→PDF
  python PDFgj.py -ir          图片→PDF(递归)      python PDFgj.py -w          Word→PDF
  python PDFgj.py -wr          Word→PDF(递归)      python PDFgj.py -e          Excel→PDF
  python PDFgj.py -er          Excel→PDF(递归)     python PDFgj.py -p          PPT→PDF
  python PDFgj.py -pr          PPT→PDF(递归)       python PDFgj.py -p --slides 1,3,5-8  PPT→PDF(指定页码)
  python PDFgj.py -ro out      合并+递归+指定输出
  python -m pdfgj              合并PDF(新入口)     python -m pdfgj -i          图片→PDF(新入口)
        ''',
```

- [ ] **Step 3: 更新 -o/--sortby 的参数校验**

将 `cli.py` 第 66-69 行：
```python
    has_output = _argv_has(('-o', '--output'))
    has_sortby = _argv_has('--sortby')
    if (has_output or has_sortby) and not args.merge:
        p.error('-o / --sortby 只能在合并模式 (-m) 下使用')
```
替换为：
```python
    has_output = _argv_has(('-o', '--output'))
    has_sortby = _argv_has('--sortby')
    # 默认模式和 -m 都是合并，都允许使用 -o / --sortby
    is_merge = args.merge or (not args.image and not args.word and not args.excel and not args.ppt)
    if (has_output or has_sortby) and not is_merge:
        p.error('-o / --sortby 只能在合并模式下使用')
```

- [ ] **Step 4: 语法检查**

Run: `python -m py_compile pdfgj/cli.py`
Expected: 无输出（编译成功）

---

### Task 3: 修改 cli.py — main() 分支逻辑重排

**Files:**
- Modify: `pdfgj/cli.py:86-148` (main 函数)

- [ ] **Step 1: 将图片转 PDF 分支改为 args.image**

将 `cli.py` 第 133-147 行的图片转 PDF 分支：
```python
    # --- 图片转 PDF（默认模式，支持递归）---
    images = _get_files(cwd, IMG_FORMATS, recursive=args.recursive)
    if not images:
        print("当前目录未找到图片文件")
        print(f"支持格式: {', '.join(sorted(IMG_FORMATS))}")
        return
    print(f"找到 {len(images)} 张图片\n")
    total = len(images)
    t0 = time.time()
    failed: list[str] = []
    for i, img in enumerate(images, 1):
        if not image_to_pdf(img, grayscale=args.gray):
            failed.append(img.name)
        _progress_bar(i, total, t0, "图片→PDF")
    _print_summary(len(images), failed)
```
替换为：
```python
    # --- 图片转 PDF（-i 模式）---
    if args.image:
        images = _get_files(cwd, IMG_FORMATS, recursive=args.recursive)
        if not images:
            print("当前目录未找到图片文件")
            print(f"支持格式: {', '.join(sorted(IMG_FORMATS))}")
            return
        print(f"找到 {len(images)} 张图片\n")
        total = len(images)
        t0 = time.time()
        failed: list[str] = []
        for i, img in enumerate(images, 1):
            if not image_to_pdf(img):
                failed.append(img.name)
            _progress_bar(i, total, t0, "图片→PDF")
        _print_summary(len(images), failed)
        return
```

- [ ] **Step 2: 将合并分支移到末尾作为默认 fallback**

将 `cli.py` 第 95-98 行的合并分支：
```python
    # --- 合并 PDF ---
    if args.merge:
        merge_pdfs(cwd, output_name=args.output, recursive=args.recursive, sortby=args.sortby)
        return
```
**删除**，然后在 main() 函数末尾（图片转 PDF 分支之后）添加：
```python
    # --- 合并 PDF（默认模式，包括 -m 显式指定）---
    merge_pdfs(cwd, output_name=args.output, recursive=args.recursive, sortby=args.sortby)
```

最终 main() 函数的分支顺序应为：
1. Word 转 PDF (`if args.word`)
2. Excel 转 PDF (`if args.excel`)
3. PPT 转 PDF (`if args.ppt`)
4. 图片转 PDF (`if args.image`)
5. 合并 PDF（默认 fallback，无 `if` 条件）

- [ ] **Step 3: 语法检查**

Run: `python -m py_compile pdfgj/cli.py`
Expected: 无输出（编译成功）

---

### Task 4: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新模式描述**

将 `CLAUDE.md` 第 49-53 行：
```
**四种互斥模式**（通过 argparse 互斥组实现）：
- **图片转 PDF**（默认/`-g`）：`image_convert.py`，使用 Pillow，自动处理 RGBA/P→RGB
- **Word 转 PDF**（`-w`）：`word_convert.py`，COM 自动化 `Word.Application`
- **Excel 转 PDF**（`-e`）：`excel_convert.py`，COM 自动化 `Excel.Application`
- **PDF 合并**（`-m`）：`merge.py`，使用 pypdf `PdfWriter`
```
替换为：
```
**五种互斥模式**（通过 argparse 互斥组实现，默认为合并）：
- **PDF 合并**（默认/`-m`）：`merge.py`，使用 pypdf `PdfWriter`
- **图片转 PDF**（`-i`）：`image_convert.py`，使用 Pillow，自动处理 RGBA/P→RGB
- **Word 转 PDF**（`-w`）：`word_convert.py`，COM 自动化 `Word.Application`
- **Excel 转 PDF**（`-e`）：`excel_convert.py`，COM 自动化 `Excel.Application`
- **PPT 转 PDF**（`-p`）：`ppt_convert.py`，COM 自动化 `PowerPoint.Application`
```

- [ ] **Step 2: 语法检查（文档无语法，跳过）**

---

### Task 5: 端到端验证

**Files:** 无（只运行命令）

- [ ] **Step 1: 验证默认模式是合并**

Run: `python -m pdfgj -h`
Expected: 帮助信息中 `-i` 出现在图片模式，无 `-g` 参数，epilog 示例中默认行为为"合并PDF"

- [ ] **Step 2: 验证 -i 参数存在**

Run: `python -m pdfgj -h 2>&1 | grep -i "\-i"`
Expected: 包含 `-i, --image` 的行

- [ ] **Step 3: 验证 -g 参数已移除**

Run: `python -m pdfgj -h 2>&1 | grep -i "\-g"`
Expected: 无输出（-g 已不存在）

- [ ] **Step 4: 全量语法检查**

Run: `python -m py_compile pdfgj/cli.py && python -m py_compile pdfgj/image_convert.py && echo "OK"`
Expected: `OK`

- [ ] **Step 5: 提交**

```bash
git add pdfgj/cli.py pdfgj/image_convert.py CLAUDE.md docs/superpowers/specs/2026-05-14-cli-default-mode-redesign.md docs/superpowers/plans/2026-05-14-cli-default-mode-redesign.md
git commit -m "refactor: 默认模式改为PDF合并，图片转PDF改用-i参数，去掉灰度功能"
```
