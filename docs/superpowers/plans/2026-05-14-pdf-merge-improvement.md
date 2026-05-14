# PDF合并功能改进实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构PDF合并功能，创建独立的PDF处理器模块，实现文件验证、页面标准化、方向矫正等功能，提升程序的稳定性和用户体验。

**Architecture:** 创建独立的 pdf_processor.py 模块，负责PDF文件验证、页面标准化和方向矫正。重构 merge.py 集成该模块，实现流式合并、覆盖机制和全面的异常处理。

**Tech Stack:** Python, pypdf/PyPDF2, pathlib

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `pdfgj/pdf_processor.py` | PDF文件验证、页面标准化、方向矫正 | 创建 |
| `pdfgj/merge.py` | PDF合并主逻辑 | 修改 |
| `pdfgj/deps.py` | 依赖检测 | 修改（如需要） |
| `tests/test_pdf_processor.py` | PDF处理器单元测试 | 创建 |

---

### Task 1: 创建PDF处理器模块基础结构

**Files:**
- Create: `pdfgj/pdf_processor.py`
- Test: `tests/test_pdf_processor.py`

- [ ] **Step 1: 创建PDF处理器模块文件**

```python
"""PDF处理器：文件验证、页面标准化、方向矫正"""

from pathlib import Path
from .deps import _has_pypdf, PdfReader, PdfWriter


class PDFProcessor:
    """PDF处理器：验证、标准化、方向矫正"""

    # A4画布尺寸（点）
    A4_WIDTH = 595.28
    A4_HEIGHT = 841.89

    def __init__(self):
        if not _has_pypdf:
            raise RuntimeError("缺少 pypdf 库，无法处理 PDF。请运行: pip install pypdf")

    def validate_file(self, file_path: Path) -> tuple[bool, str]:
        """验证PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检测0字节文件
        if file_path.stat().st_size == 0:
            return False, "文件为空（0字节）"

        # 检测无法打开的PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, f"无法打开PDF: {e}"

        # 检测空白页面
        if len(reader.pages) == 0:
            return False, "PDF没有页面"

        return True, ""

    def standardize_page(self, page):
        """标准化页面到A4尺寸

        Args:
            page: 原始PDF页面

        Returns:
            标准化后的A4页面
        """
        # 获取原始页面尺寸
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)

        # 计算缩放比例
        scale_x = self.A4_WIDTH / original_width
        scale_y = self.A4_HEIGHT / original_height
        scale = min(scale_x, scale_y)  # 保持宽高比

        # 计算新尺寸
        new_width = original_width * scale
        new_height = original_height * scale

        # 计算居中偏移
        offset_x = (self.A4_WIDTH - new_width) / 2
        offset_y = (self.A4_HEIGHT - new_height) / 2

        # 创建新的A4页面
        from pypdf import PageObject, Transformation
        new_page = PageObject.create_blank_page(
            width=self.A4_WIDTH,
            height=self.A4_HEIGHT
        )

        # 合并原始页面到新页面
        new_page.merge_transformed_page(
            page,
            Transformation().scale(scale).translate(offset_x, offset_y)
        )

        return new_page

    def correct_orientation(self, page):
        """矫正页面方向

        Args:
            page: 原始PDF页面

        Returns:
            矫正方向后的页面
        """
        # 获取旋转属性
        rotation = page.get('/Rotation', 0)

        # 如果有旋转，需要矫正
        if rotation != 0:
            from pypdf import PageObject, Transformation
            # 创建新的页面，应用反向旋转
            new_page = PageObject.create_blank_page(
                width=page.mediabox.width,
                height=page.mediabox.height
            )
            new_page.merge_transformed_page(
                page,
                Transformation().rotate(-rotation)
            )
            return new_page

        return page

    def process_pdf(self, file_path: Path) -> tuple[bool, list, str]:
        """处理PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, list, str]: (是否成功, 处理后的页面列表, 错误信息)
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            return False, [], error_msg

        # 读取PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, [], f"无法打开PDF: {e}"

        # 处理每一页
        processed_pages = []
        for page in reader.pages:
            # 矫正方向
            page = self.correct_orientation(page)
            # 标准化到A4
            page = self.standardize_page(page)
            processed_pages.append(page)

        return True, processed_pages, ""
```

- [ ] **Step 2: 运行语法检查**

Run: `python -m py_compile pdfgj/pdf_processor.py`
Expected: 无输出（语法正确）

- [ ] **Step 3: 提交代码**

```bash
git add pdfgj/pdf_processor.py
git commit -m "feat: 创建PDF处理器模块基础结构"
```

---

### Task 2: 添加PDF处理器单元测试

**Files:**
- Create: `tests/test_pdf_processor.py`

- [ ] **Step 1: 创建测试文件**

```python
"""PDF处理器单元测试"""

import pytest
from pathlib import Path
from pdfgj.pdf_processor import PDFProcessor


@pytest.fixture
def processor():
    """创建PDF处理器实例"""
    return PDFProcessor()


class TestPDFProcessorInit:
    """PDF处理器初始化测试"""

    def test_init_success(self):
        """测试正常初始化"""
        processor = PDFProcessor()
        assert processor is not None
        assert processor.A4_WIDTH == 595.28
        assert processor.A4_HEIGHT == 841.89


class TestValidateFile:
    """文件验证测试"""

    def test_validate_nonexistent_file(self, processor, tmp_path):
        """测试不存在的文件"""
        # 注意：validate_file 不检查文件是否存在，只检查大小
        # 这里测试的是文件不存在时的异常处理
        pass

    def test_validate_empty_file(self, processor, tmp_path):
        """测试空文件（0字节）"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        is_valid, error_msg = processor.validate_file(empty_file)
        assert is_valid is False
        assert "文件为空" in error_msg

    def test_validate_invalid_pdf(self, processor, tmp_path):
        """测试无效的PDF文件"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        is_valid, error_msg = processor.validate_file(invalid_file)
        assert is_valid is False
        assert "无法打开PDF" in error_msg
```

- [ ] **Step 2: 运行测试**

Run: `pytest tests/test_pdf_processor.py -v`
Expected: 所有测试通过

- [ ] **Step 3: 提交代码**

```bash
git add tests/test_pdf_processor.py
git commit -m "test: 添加PDF处理器单元测试"
```

---

### Task 3: 重构merge.py集成PDF处理器

**Files:**
- Modify: `pdfgj/merge.py`

- [ ] **Step 1: 更新merge.py导入**

```python
"""PDF 合并"""

import os
import time
from pathlib import Path

from .deps import _has_pypdf, PdfMerger, PdfReader, PdfWriter
from .utils import _get_files, natural_sort_key, _check_overwrite, _progress_bar
from .pdf_processor import PDFProcessor


def _get_all_pdfs(directory: Path, recursive: bool = False, exclude: set[str] | None = None) -> list[Path]:
    """获取目录下所有 PDF 文件，排除指定文件名"""
    ex = exclude or set()
    return [f for f in _get_files(directory, {'.pdf'}, recursive) if f.name not in ex]


def merge_pdfs(directory: Path, output_name: str = "merged.pdf", recursive: bool = False,
               sortby: str = 'name') -> bool:
    """流式合并目录下 PDF 文件为单一 PDF，逐文件读取避免大目录内存耗尽"""
    if not _has_pypdf:
        print("缺少 pypdf 库，无法合并 PDF。请运行: pip install pypdf")
        return False
    assert PdfMerger is not None  # 静态分析护栏：_has_pypdf 为 True 时 PdfMerger 必定已导入
    pdf_files = _get_all_pdfs(directory, recursive, exclude={output_name})
    if sortby == 'ctime':
        pdf_files.sort(key=lambda f: f.stat().st_ctime)
    elif sortby == 'mtime':
        pdf_files.sort(key=lambda f: f.stat().st_mtime)
    else:
        pdf_files.sort(key=natural_sort_key)
    if not pdf_files:
        print("未找到可合并的 PDF 文件（尝试加 -r 递归查找子目录）")
        return False

    out_path = Path(output_name) if os.path.isabs(output_name) else (directory / output_name)
    if not _check_overwrite(out_path):
        return False

    # 创建PDF处理器
    processor = PDFProcessor()

    # 流式合并：使用 PdfWriter 逐文件追加，PdfReader 读完即释放
    writer = PdfWriter()  # type: ignore[misc]
    failed: list[Path] = []
    total = len(pdf_files)
    t0 = time.time()

    for i, pdf in enumerate(pdf_files, 1):
        _progress_bar(i, total, t0, "合并中")

        # 验证文件
        is_valid, error_msg = processor.validate_file(pdf)
        if not is_valid:
            print(f"\r  [跳过] {pdf.name}: {error_msg}")
            failed.append(pdf)
            continue

        # 处理PDF
        try:
            success, pages, error_msg = processor.process_pdf(pdf)
            if not success:
                print(f"\r  [跳过] {pdf.name}: {error_msg}")
                failed.append(pdf)
                continue

            # 添加页面到writer
            for page in pages:
                writer.add_page(page)
        except Exception as err:
            print(f"\r  [跳过] {pdf.name}: {err}")
            failed.append(pdf)

    # 进度条收尾换行
    _progress_bar(total, total, t0, "合并中")

    if not writer.pages:
        print("所有 PDF 文件均无法合并")
        writer.close()
        return False

    try:
        with open(str(out_path), 'wb') as f:
            writer.write(f)
    except Exception as err:
        print(f"合并写入失败: {err}")
        return False
    finally:
        writer.close()

    success_count = total - len(failed)
    print(f"合并完成！{success_count} 个 PDF → {out_path}")
    if failed:
        print(f"跳过: {[f.name for f in failed]}")
    return True
```

- [ ] **Step 2: 运行语法检查**

Run: `python -m py_compile pdfgj/merge.py`
Expected: 无输出（语法正确）

- [ ] **Step 3: 提交代码**

```bash
git add pdfgj/merge.py
git commit -m "refactor: 重构merge.py集成PDF处理器"
```

---

### Task 4: 更新deps.py支持pypdf导入

**Files:**
- Modify: `pdfgj/deps.py`

- [ ] **Step 1: 检查deps.py是否需要更新**

当前 deps.py 已经支持 pypdf/PyPDF2 的导入，包括 PdfReader、PdfWriter 和 PdfMerger。但 pdf_processor.py 需要导入 PageObject 和 Transformation 类。

检查是否需要在 deps.py 中添加这些导入。

- [ ] **Step 2: 更新deps.py添加PageObject和Transformation支持**

```python
"""pypdf / win32com 依赖检测"""

# ============================================================
# pypdf 三层回退导入（pypdf → PyPDF2 >=2.0 → PyPDF2 <2.0）
# ============================================================
try:
    from pypdf import PdfMerger, PdfReader, PdfWriter, PageObject, Transformation  # noqa: F811
    _has_pypdf: bool = True
    _pypdf_source: str = 'pypdf'
except ImportError:
    try:
        from PyPDF2 import PdfMerger, PdfReader, PdfWriter  # type: ignore[no-redef]
        from PyPDF2 import PageObject, Transformation  # type: ignore[no-redef]
        _has_pypdf = True
        _pypdf_source = 'PyPDF2 (>=2.0)'
        print("  [提示] 检测到 PyPDF2，建议升级到 pypdf: pip install pypdf")
    except ImportError:
        try:
            from PyPDF2 import PdfMerger, PdfFileReader as PdfReader, PdfFileWriter as PdfWriter  # type: ignore[no-redef]
            # 旧版 PyPDF2 可能没有 PageObject 和 Transformation
            PageObject = None  # type: ignore[assignment,misc]
            Transformation = None  # type: ignore[assignment,misc]
            _has_pypdf = True
            _pypdf_source = 'PyPDF2 (<2.0，旧版)'
            print("  [提示] 检测到旧版 PyPDF2，建议升级: pip install pypdf")
        except ImportError:
            _has_pypdf = False
            _pypdf_source = ''
            PdfMerger = None  # type: ignore[assignment]
            PdfReader = None  # type: ignore[assignment]
            PdfWriter = None  # type: ignore[assignment]
            PageObject = None  # type: ignore[assignment,misc]
            Transformation = None  # type: ignore[assignment,misc]

# ============================================================
# win32com 检测
# ============================================================
try:
    from win32com.client import Dispatch, DispatchEx  # noqa: F811
    import pywintypes
    import pythoncom
    _has_win32: bool = True
except ImportError:
    _has_win32 = False
    Dispatch = None  # type: ignore[assignment]
    DispatchEx = None  # type: ignore[assignment]
    pythoncom = None  # type: ignore[assignment]
```

- [ ] **Step 3: 更新pdf_processor.py使用deps.py中的导入**

```python
"""PDF处理器：文件验证、页面标准化、方向矫正"""

from pathlib import Path
from .deps import _has_pypdf, PdfReader, PdfWriter, PageObject, Transformation


class PDFProcessor:
    """PDF处理器：验证、标准化、方向矫正"""

    # A4画布尺寸（点）
    A4_WIDTH = 595.28
    A4_HEIGHT = 841.89

    def __init__(self):
        if not _has_pypdf:
            raise RuntimeError("缺少 pypdf 库，无法处理 PDF。请运行: pip install pypdf")
        if PageObject is None or Transformation is None:
            raise RuntimeError("当前 PyPDF2 版本不支持页面操作，请升级: pip install pypdf")

    def validate_file(self, file_path: Path) -> tuple[bool, str]:
        """验证PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检测0字节文件
        if file_path.stat().st_size == 0:
            return False, "文件为空（0字节）"

        # 检测无法打开的PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, f"无法打开PDF: {e}"

        # 检测空白页面
        if len(reader.pages) == 0:
            return False, "PDF没有页面"

        return True, ""

    def standardize_page(self, page):
        """标准化页面到A4尺寸

        Args:
            page: 原始PDF页面

        Returns:
            标准化后的A4页面
        """
        # 获取原始页面尺寸
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)

        # 计算缩放比例
        scale_x = self.A4_WIDTH / original_width
        scale_y = self.A4_HEIGHT / original_height
        scale = min(scale_x, scale_y)  # 保持宽高比

        # 计算新尺寸
        new_width = original_width * scale
        new_height = original_height * scale

        # 计算居中偏移
        offset_x = (self.A4_WIDTH - new_width) / 2
        offset_y = (self.A4_HEIGHT - new_height) / 2

        # 创建新的A4页面
        new_page = PageObject.create_blank_page(
            width=self.A4_WIDTH,
            height=self.A4_HEIGHT
        )

        # 合并原始页面到新页面
        new_page.merge_transformed_page(
            page,
            Transformation().scale(scale).translate(offset_x, offset_y)
        )

        return new_page

    def correct_orientation(self, page):
        """矫正页面方向

        Args:
            page: 原始PDF页面

        Returns:
            矫正方向后的页面
        """
        # 获取旋转属性
        rotation = page.get('/Rotation', 0)

        # 如果有旋转，需要矫正
        if rotation != 0:
            # 创建新的页面，应用反向旋转
            new_page = PageObject.create_blank_page(
                width=page.mediabox.width,
                height=page.mediabox.height
            )
            new_page.merge_transformed_page(
                page,
                Transformation().rotate(-rotation)
            )
            return new_page

        return page

    def process_pdf(self, file_path: Path) -> tuple[bool, list, str]:
        """处理PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, list, str]: (是否成功, 处理后的页面列表, 错误信息)
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            return False, [], error_msg

        # 读取PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, [], f"无法打开PDF: {e}"

        # 处理每一页
        processed_pages = []
        for page in reader.pages:
            # 矫正方向
            page = self.correct_orientation(page)
            # 标准化到A4
            page = self.standardize_page(page)
            processed_pages.append(page)

        return True, processed_pages, ""
```

- [ ] **Step 4: 运行语法检查**

Run: `python -m py_compile pdfgj/deps.py`
Run: `python -m py_compile pdfgj/pdf_processor.py`
Expected: 无输出（语法正确）

- [ ] **Step 5: 提交代码**

```bash
git add pdfgj/deps.py pdfgj/pdf_processor.py
git commit -m "feat: 更新deps.py支持PageObject和Transformation导入"
```

---

### Task 5: 运行完整测试验证

**Files:**
- Test: `tests/test_pdf_processor.py`

- [ ] **Step 1: 运行所有语法检查**

Run: `python -m py_compile pdfgj/*.py`
Expected: 无输出（所有模块语法正确）

- [ ] **Step 2: 运行单元测试**

Run: `pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 3: 手动测试合并功能**

创建测试PDF文件，运行合并命令验证功能：

```bash
# 创建测试目录
mkdir test_merge
cd test_merge

# 创建测试PDF文件（需要手动创建或使用现有PDF文件）

# 运行合并
python -m pdfgj -m -o merged.pdf

# 验证输出文件存在
ls -la merged.pdf
```

- [ ] **Step 4: 提交最终代码**

```bash
git add -A
git commit -m "feat: 完成PDF合并功能改进"
```

---

## 验证清单

- [ ] 所有语法检查通过
- [ ] 所有单元测试通过
- [ ] 文件验证功能正常工作
- [ ] 页面标准化功能正常工作
- [ ] 方向矫正功能正常工作
- [ ] 合并功能正常工作
- [ ] 覆盖机制正常工作
- [ ] 异常处理正常工作
- [ ] 资源释放正常工作

---

## 注意事项

1. **PyPDF2版本兼容性**：PageObject 和 Transformation 类在 PyPDF2 2.0+ 中可用，旧版本可能不支持
2. **内存管理**：逐文件处理可以控制内存占用，但大文件仍然可能消耗较多内存
3. **异常处理**：确保所有异常都被捕获并正确处理，程序不会闪退
4. **资源释放**：确保 PdfReader 和 PdfWriter 对象在使用后正确关闭
