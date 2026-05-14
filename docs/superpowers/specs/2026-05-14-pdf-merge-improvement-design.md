# PDF合并功能改进设计文档

## 1. 概述

本文档描述PDF合并功能的改进方案，旨在提升程序的稳定性、可靠性和用户体验。

## 2. 需求分析

### 2.1 用户需求

1. 采用Python开发，代码遵循生产规范，程序整体稳定性强
2. 自动筛查剔除无效、空白以及损坏文件
3. 文件依照文件名数字补零规则排序，保证排列顺序准确无误
4. 统一设置固定A4画布尺寸，各类规格页面居中摆放，小页面自动留白，大页面等比例适配，保证内容完整无变形
5. 采用流式合并方式处理大体积文件，分批加载内容，控制内存占用，防止程序卡顿崩溃
6. 配备文件防覆盖机制，输出前校验文件是否存在，已有文件则作出提醒，禁止直接覆盖保存
7. 覆盖各类运行异常捕获机制，应对路径、权限、文件损坏、磁盘空间不足等问题，程序运行稳定不闪退
8. 运行结束自动释放各类资源，有效规避内存泄漏问题
9. 处理好横屏竖屏的问题，不要出现字形是倒着的情况

### 2.2 澄清结果

- **页面适配**：等比缩放+居中+留白
- **方向处理**：自动矫正方向
- **文件检测**：基础检测（0字节文件、无法打开的PDF、页面内容为空的PDF）
- **内存控制**：逐文件处理
- **覆盖机制**：交互式确认
- **模块设计**：独立处理器模块

## 3. 架构设计

### 3.1 模块结构

```
pdfgj/
├── deps.py              # 依赖检测
├── utils.py             # 工具函数
├── constants.py         # 常量定义
├── com_core.py          # COM核心
├── image_convert.py     # 图片转换
├── word_convert.py      # Word转换
├── excel_convert.py     # Excel转换
├── ppt_convert.py       # PPT转换
├── pdf_processor.py     # PDF处理器（新增）
├── merge.py             # PDF合并（重构）
└── cli.py               # 命令行接口
```

### 3.2 新增模块：pdf_processor.py

负责PDF文件的验证、页面标准化和方向矫正。

#### 3.2.1 主要功能

1. **文件验证**
   - 检测0字节文件
   - 检测无法打开的PDF
   - 检测空白页面

2. **页面标准化**
   - A4画布尺寸：595.28 x 841.89 点（210 x 297 毫米）
   - 等比缩放+居中+留白

3. **方向矫正**
   - 检测页面的/Rotation属性
   - 自动矫正方向

#### 3.2.2 类设计

```python
class PDFProcessor:
    """PDF处理器：验证、标准化、方向矫正"""

    A4_WIDTH = 595.28   # A4宽度（点）
    A4_HEIGHT = 841.89  # A4高度（点）

    def __init__(self):
        pass

    def validate_file(self, file_path: Path) -> tuple[bool, str]:
        """验证PDF文件"""
        # 检测0字节文件
        # 检测无法打开的PDF
        # 检测空白页面
        pass

    def standardize_page(self, page) -> object:
        """标准化页面到A4尺寸"""
        # 等比缩放+居中+留白
        pass

    def correct_orientation(self, page) -> object:
        """矫正页面方向"""
        # 检测/Rotation属性
        # 自动矫正方向
        pass

    def process_pdf(self, file_path: Path) -> tuple[bool, list[object], str]:
        """处理PDF文件，返回验证结果、标准化页面和错误信息"""
        pass
```

### 3.3 重构merge.py

#### 3.3.1 改进点

1. 集成PDFProcessor
2. 流式合并：逐文件处理
3. 覆盖机制：交互式确认
4. 异常捕获：全面覆盖各种异常
5. 资源释放：确保所有资源正确释放

#### 3.3.2 函数设计

```python
def merge_pdfs(directory: Path, output_name: str = "merged.pdf", 
               recursive: bool = False, sortby: str = 'name') -> bool:
    """流式合并目录下 PDF 文件为单一 PDF"""
    # 1. 验证输出路径
    # 2. 获取PDF文件列表
    # 3. 排序文件
    # 4. 创建PDF处理器
    # 5. 流式合并
    # 6. 写入输出文件
    # 7. 释放资源
    pass
```

## 4. 详细设计

### 4.1 文件验证

```python
def validate_file(self, file_path: Path) -> tuple[bool, str]:
    """验证PDF文件"""
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
```

### 4.2 页面标准化

```python
def standardize_page(self, page) -> object:
    """标准化页面到A4尺寸"""
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
```

### 4.3 方向矫正

```python
def correct_orientation(self, page) -> object:
    """矫正页面方向"""
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
```

### 4.4 流式合并

```python
def merge_pdfs(directory: Path, output_name: str = "merged.pdf",
               recursive: bool = False, sortby: str = 'name') -> bool:
    """流式合并目录下 PDF 文件为单一 PDF"""
    # 验证输出路径
    out_path = Path(output_name) if os.path.isabs(output_name) else (directory / output_name)
    if not _check_overwrite(out_path):
        return False

    # 获取PDF文件列表
    pdf_files = _get_all_pdfs(directory, recursive, exclude={output_name})
    if not pdf_files:
        print("未找到可合并的 PDF 文件")
        return False

    # 排序文件
    if sortby == 'ctime':
        pdf_files.sort(key=lambda f: f.stat().st_ctime)
    elif sortby == 'mtime':
        pdf_files.sort(key=lambda f: f.stat().st_mtime)
    else:
        pdf_files.sort(key=natural_sort_key)

    # 创建PDF处理器
    processor = PDFProcessor()

    # 流式合并
    writer = PdfWriter()
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

    # 进度条收尾
    _progress_bar(total, total, t0, "合并中")

    # 检查是否有页面
    if not writer.pages:
        print("所有 PDF 文件均无法合并")
        writer.close()
        return False

    # 写入输出文件
    try:
        with open(str(out_path), 'wb') as f:
            writer.write(f)
    except Exception as err:
        print(f"合并写入失败: {err}")
        return False
    finally:
        writer.close()

    # 输出统计
    success_count = total - len(failed)
    print(f"合并完成！{success_count} 个 PDF → {out_path}")
    if failed:
        print(f"跳过: {[f.name for f in failed]}")
    return True
```

## 5. 异常处理

### 5.1 异常类型

1. **文件系统异常**
   - 路径不存在
   - 权限不足
   - 磁盘空间不足

2. **PDF文件异常**
   - 文件损坏
   - 格式错误
   - 加密文件

3. **内存异常**
   - 内存不足
   - 大文件处理

### 5.2 异常处理策略

```python
try:
    # 主要逻辑
except FileNotFoundError:
    print(f"错误：文件不存在 - {file_path}")
except PermissionError:
    print(f"错误：权限不足 - {file_path}")
except OSError as e:
    if "No space left" in str(e):
        print("错误：磁盘空间不足")
    else:
        print(f"文件系统错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
finally:
    # 释放资源
```

## 6. 资源管理

### 6.1 资源类型

1. **PdfReader对象**
   - 打开文件后需要关闭
   - 使用finally确保关闭

2. **PdfWriter对象**
   - 写入完成后需要关闭
   - 使用finally确保关闭

3. **文件句柄**
   - 使用with语句自动关闭

### 6.2 资源释放策略

```python
reader = None
try:
    reader = PdfReader(str(file_path))
    # 处理逻辑
except Exception as e:
    # 异常处理
finally:
    if reader is not None:
        try:
            reader.stream.close()
        except Exception:
            pass
```

## 7. 测试策略

### 7.1 单元测试

1. **文件验证测试**
   - 0字节文件
   - 损坏文件
   - 空白页面

2. **页面标准化测试**
   - 不同尺寸页面
   - 不同方向页面

3. **方向矫正测试**
   - 0度旋转
   - 90度旋转
   - 180度旋转
   - 270度旋转

### 7.2 集成测试

1. **合并功能测试**
   - 正常合并
   - 异常文件处理
   - 大文件处理

2. **覆盖机制测试**
   - 文件不存在
   - 文件存在，用户确认覆盖
   - 文件存在，用户拒绝覆盖

## 8. 实施计划

### 8.1 阶段1：创建PDF处理器模块

- 创建pdf_processor.py
- 实现文件验证功能
- 实现页面标准化功能
- 实现方向矫正功能

### 8.2 阶段2：重构merge.py

- 集成PDFProcessor
- 实现流式合并
- 实现覆盖机制
- 完善异常处理

### 8.3 阶段3：测试和优化

- 编写单元测试
- 编写集成测试
- 性能优化
- 文档更新

## 9. 总结

本设计方案通过创建独立的PDF处理器模块，实现了文件验证、页面标准化和方向矫正等功能，同时重构了merge.py以支持流式合并、覆盖机制和全面的异常处理。该方案提高了程序的稳定性、可靠性和用户体验。
