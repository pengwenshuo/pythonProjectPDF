# PPT 转 PDF 功能设计

## 概述

为 PDFgj 工具添加 PowerPoint 演示文稿转 PDF 功能，复用现有 COM 自动化架构，支持全量导出和指定页码范围导出。

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `pdfgj/constants.py` | 修改 | 添加 `PPT_FORMATS`、PPT COM 常量 |
| `pdfgj/utils.py` | 修改 | 添加 `parse_slide_range()` 页码范围解析函数 |
| `pdfgj/ppt_convert.py` | 新建 | PPT 转 PDF 核心逻辑 |
| `pdfgj/cli.py` | 修改 | 添加 `-p/--ppt` 和 `--slides` 参数 |
| `pdfgj/com_core.py` | 修改 | 添加 `PowerPoint.Application` 进程名映射 |

不改动 `word_convert.py`、`excel_convert.py`、`merge.py`、`deps.py`。

## 常量定义

### constants.py

```python
PPT_FORMATS: set[str] = {'.pptx', '.ppt'}

# PowerPoint: PpSaveAsFileType 枚举
PP_SAVE_AS_PDF: int = 32  # ppSaveAsPDF
# PowerPoint: PpSlideShowRangeType 枚举
PP_SLIDE_SHOW_ALL: int = 1  # ppSlideShowAll
```

### com_core.py

`_COM_PROCESS_NAMES` 添加：

```python
'PowerPoint.Application': 'POWERPNT.EXE',
```

## ppt_convert.py 核心逻辑

结构对齐 `word_convert.py`，四个核心组件：

### _setup_ppt(ppt)

配置 PowerPoint 应用：
- `Visible = False`
- `DisplayAlerts = False`

### _convert_ppt(ppt, ppt_path, slides=None)

转换单个文件：
- `slides=None`：导出全部（`RangeType=1`）
- `slides="1,3,5-8"`：解析页码后设置 `RangeType=3`，创建 `PrintRanges` 对象

调用 `presentation.ExportAsFixedFormat()`：
```python
presentation.ExportAsFixedFormat(
    Path=32,                      # ppSaveAsPDF
    OutputFileName=str(pdf_path),
    Intent=2,                     # ppIntentScreen
    FrameSlides=0,                # msoFalse
    HandoutOrder=1,               # ppPrintHandoutVerticalFirst
    OutputType=1,                 # ppPrintOutputSlides
    PrintRange=None,              # 指定范围时用 PrintRange 对象
    RangeType=range_type,         # 1=全部, 3=指定范围
    SlideShowName=None,
    IncludeDocProperties=True,
    KeepIRMSettings=True,
    DocStructureTags=True,
    BitmapMissingFonts=True,
    UseISO19005_1=False,
    IncludeMarkup=False,
    ExternalExporter=None
)
```

### ppt_to_pdf(ppt_path, slides=None)

单文件模式：启动 PowerPoint → 转换 → 退出（兼容独立调用）。

### PptConverter 类

上下文管理器，批量转换复用同一实例：

```python
class PptConverter:
    def __init__(self, slides: str | None = None):
        self._slides = slides
        # ...

    def __enter__(self) -> 'PptConverter':
        # CoInitialize + DispatchEx('PowerPoint.Application')
        # _setup_ppt(self._app)
        pass

    def __exit__(self, *args) -> None:
        # _com_quit + CoUninitialize
        pass

    def convert(self, path: Path | str) -> bool:
        # _convert_ppt(self._app, Path(path), self._slides)
        pass
```

## 页码范围解析

### utils.py 中添加 parse_slide_range()

```python
def parse_slide_range(spec: str, total_slides: int) -> list[int]:
    """
    解析页码范围字符串，返回去重排序后的页码列表。

    格式: "1,3,5-8,10"
    规则:
      - 页码从 1 开始
      - 支持单页 (3) 和范围 (5-8)
      - 超出 total_slides 的页码会被裁剪并警告
      - 空字符串或无效格式抛出 ValueError

    示例:
      parse_slide_range("1,3,5-8", 10) → [1, 3, 5, 6, 7, 8]
      parse_slide_range("3-1", 10) → ValueError("起始页不能大于结束页")
    """
```

调用位置：`_convert_ppt()` 内部，在 `ExportAsFixedFormat` 之前。

## CLI 集成

### 互斥组添加 -p

```python
mode.add_argument('-p', '--ppt', action='store_true', help='PPT 模式：PowerPoint 演示文稿转 PDF')
```

### 添加 --slides 参数

```python
p.add_argument('--slides', type=str, default=None,
               help='PPT 模式：指定导出页码，如 "1,3,5-8"')
```

### 参数校验

```python
if _argv_has('--slides') and not args.ppt:
    p.error('--slides 只能在 PPT 模式 (-p) 下使用')
```

### 主流程 PPT 分支

```python
if args.ppt:
    files = _get_files(cwd, PPT_FORMATS, recursive=args.recursive)
    if not files:
        print("当前目录未找到 PowerPoint 演示文稿 (.pptx / .ppt)")
        return
    print(f"找到 {len(files)} 个演示文稿")
    failed = _batch_convert(files, lambda: PptConverter(slides=args.slides), "PPT→PDF")
    _print_summary(len(files), failed)
    return
```

### 帮助文本更新

在 epilog 中添加：
```
  runPDF -p                   PPT→PDF
  runPDF -pr                  PPT→PDF(递归)
  runPDF -p --slides 1,3,5-8  PPT→PDF(指定页码)
```

## 错误处理

### HRESULT 映射

在 `_classify_com_error()` 中追加 PPT 特有错误码：

| HRESULT | 含义 |
|---------|------|
| `0x80080005` | PowerPoint 服务器不可用（未安装或损坏） |
| `0x80004001` | 未实现（通常是文件格式不支持） |
| `0x800A03EC` | 文件不存在或路径无效（与 Word/Excel 共享） |

### --slides 参数校验

- 格式无效 → 抛出 `ValueError`，CLI 层捕获并打印友好提示
- 页码超出范围 → 裁剪到有效范围并打印警告
- 所有页码都被裁剪 → 视为失败

## 使用示例

```bash
# 全量导出
pdfgj -p

# 递归全量导出
pdfgj -pr

# 指定页码
pdfgj -p --slides 1,3,5-8

# 指定输出目录（与其他模式一致）
pdfgj -p -r
```

## 设计决策

1. **方案选择**：复用现有模式（方案 A），不抽取基类。理由：3 个 COM 转换器的重复代码量可控，重构收益不足以覆盖风险。
2. **页码参数**：使用 `--slides` 而非 `--pages`，与 PowerPoint 术语一致。
3. **格式支持**：`.pptx` + `.ppt`，与 Word/Excel 的兼容策略一致。
4. **PptConverter 构造函数**：接收 `slides` 参数，批量转换时所有文件共享同一页码范围。
