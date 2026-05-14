# 图片转PDF功能改进设计文档

## 概述

改进图片转PDF功能，解决当前实现中的缺陷，提升稳定性和用户体验。

## 当前缺陷

| 缺陷 | 严重程度 | 描述 |
|------|----------|------|
| GIF动图处理异常 | 致命 | `save_all=True` 会把GIF所有帧都写入PDF，生成巨大文件 |
| 不处理EXIF方向信息 | 中等 | 手机照片的EXIF旋转标记未处理，导致图片方向错误 |
| 没有图片验证 | 中等 | 损坏的图片文件会导致转换失败，没有预先检测 |
| 批量处理无进度条 | 中等 | 处理多张图片时用户看不到进度（注：cli.py已有进度条，此缺陷已修复） |
| 内存未优化 | 中等 | 大图片全部加载到内存，可能导致内存问题（注：cli.py已逐张处理，需确保资源释放） |

## 需求澄清

| 需求 | 决策 |
|------|------|
| GIF处理 | 只取第一帧 |
| EXIF方向 | 自动矫正 |
| DPI | 固定200（不改） |
| 图片验证 | 跳过并报告损坏图片 |
| 进度条 | 简单进度（当前/总数，百分比，已用时间） |
| 内存优化 | 逐张处理，处理完释放 |

## 架构设计

新增 `image_processor.py` 模块，职责分离：

```
image_processor.py  (预处理：验证、EXIF、GIF、格式转换)
      ↓
image_convert.py    (转换：调用处理器、保存PDF、进度条)
```

### image_processor.py

图片预处理器，封装所有图片处理逻辑：

- 图片验证（检查文件是否可读、格式是否支持）
- EXIF方向矫正（读取EXIF标记，自动旋转）
- GIF处理（只取第一帧）
- 图片格式统一（RGBA/P → RGB，白底填充）

### image_convert.py

图片转PDF入口模块：

- 调用 `ImageProcessor` 处理图片
- 保存为PDF
- 覆盖保护

### cli.py

批量处理入口（已有进度条支持）：

- 调用 `image_to_pdf()` 逐张处理
- 使用 `_progress_bar()` 显示进度
- 统计成功/失败数量

## 接口设计

### ImageProcessor 类

```python
class ImageProcessor:
    """图片预处理器：验证、EXIF矫正、GIF处理、格式转换"""
    
    def validate(self, image_path: Path) -> tuple[bool, str]:
        """验证图片文件是否可读、格式是否支持"""
        
    def process(self, image_path: Path) -> Image | None:
        """处理单张图片：验证 → EXIF矫正 → GIF取帧 → 格式转换"""
        
    def _fix_exif_orientation(self, img: Image) -> Image:
        """根据EXIF方向信息矫正图片旋转"""
        
    def _extract_gif_frame(self, img: Image) -> Image:
        """提取GIF第一帧"""
        
    def _normalize_mode(self, img: Image) -> Image:
        """统一图片模式：RGBA/P → RGB，白底填充"""
```

返回值设计：
- `validate()`: 返回 `(是否有效, 错误信息)` 元组
- `process()`: 成功返回处理后的 PIL Image，失败返回 `None`

### image_to_pdf 函数

```python
def image_to_pdf(image_path: Path) -> bool:
    """单张图片转 PDF"""
    pdf_path = image_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False
    
    processor = ImageProcessor()
    img = processor.process(image_path)
    if img is None:
        return False
    
    try:
        img.save(pdf_path, format="PDF", resolution=200.0)
        print(f"  [OK] {image_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        print(f"  [失败] {image_path.name}: {err}")
        return False
    finally:
        img.close()
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 文件不存在 | `validate()` 返回 `(False, "文件不存在")` |
| 文件损坏/无法打开 | `validate()` 返回 `(False, "无法打开图片: {错误}")` |
| EXIF读取失败 | 忽略EXIF，按原图处理（不报错） |
| GIF取帧失败 | 尝试直接使用原图，失败则跳过 |
| 内存不足 | 捕获 `MemoryError`，打印警告，跳过该图片 |
| 保存PDF失败 | 捕获异常，打印错误，返回 `False` |

日志输出规范：
- 正常转换：`  [OK] photo.jpg → photo.pdf`
- 跳过无效：`  [跳过] 损坏的图片.jpg: 无法打开图片`
- 转换失败：`  [失败] photo.jpg: 保存PDF失败`

## 测试策略

测试文件：`tests/test_image_processor.py`

测试用例：

```python
class TestImageProcessorInit:
    def test_init_success(self): ...

class TestValidate:
    def test_validate_nonexistent_file(self): ...      # 文件不存在
    def test_validate_unsupported_format(self): ...    # 不支持的格式
    def test_validate_corrupted_image(self): ...       # 损坏的图片
    def test_validate_valid_image(self): ...           # 正常图片

class TestProcessGif:
    def test_extract_first_frame(self): ...            # GIF只取第一帧

class TestFixExifOrientation:
    def test_exif_rotation_90(self): ...               # EXIF旋转90度
    def test_exif_no_rotation(self): ...               # 无EXIF旋转

class TestNormalizeMode:
    def test_rgba_to_rgb(self): ...                    # RGBA转RGB
    def test_palette_to_rgb(self): ...                 # P模式转RGB
    def test_rgb_unchanged(self): ...                  # RGB不变
```

测试方法：
- 使用 `tmp_path` fixture 创建临时图片文件
- 使用 Pillow 创建测试图片（不同模式、不同尺寸）
- 不依赖真实图片文件，测试可重复

## 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `pdfgj/image_processor.py` | 新增 | 图片预处理器模块 |
| `pdfgj/image_convert.py` | 修改 | 调用处理器，移除内联预处理代码 |
| `tests/test_image_processor.py` | 新增 | 图片处理器单元测试 |

## 依赖

- Pillow >= 12.0（已安装）
- 无新增依赖

## 向后兼容

- `image_to_pdf()` 函数接口不变
- 支持的图片格式不变
- 默认DPI不变（200）
- 命令行参数不变
