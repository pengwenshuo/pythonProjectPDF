# PDFgj.py 模块化重构设计规范

## 目标

将 781 行单文件 `PDFgj.py` 拆分为多模块的 `pdfgj/` 包，实现：
- 可维护性：每个模块单一职责，一屏可读（60-140 行）
- 可测试性：核心逻辑可独立导入和单元测试
- 可复用性：外部脚本可按需 import 单个模块
- 扩展性：后续新增格式转换无需改动现有模块

## 模块划分

```
PDFgj.py                  ← 薄入口（3 行），兼容旧命令行习惯
pdfgj/
    __init__.py            ← 公开 API 重新导出
    __main__.py            ← python -m pdfgj 入口
    constants.py           ← 格式常量 + COM 常量（纯数据，~30 行）
    deps.py                ← pypdf / win32com 依赖检测（~45 行）
    utils.py               ← 工具层：排序、文件获取、进度条、覆盖保护、全局标志（~70 行）
    com_core.py            ← COM 公共层：PID 获取、进程退出、错误分类、预检、批量转换器（~140 行）
    image_convert.py       ← 图片转 PDF（~30 行）
    word_convert.py        ← Word 转 PDF：配置函数 + 原子转换 + 单文件模式 + 上下文管理器（~100 行）
    excel_convert.py       ← Excel 转 PDF：配置函数 + 原子转换 + 单文件模式 + 上下文管理器（~100 行）
    merge.py               ← PDF 合并（~80 行）
    cli.py                 ← 参数解析 + 主流程（~80 行）
```

## 依赖关系

```
constants       ← 零依赖
deps            ← constants
utils           ← deps（全局标志）
com_core        ← utils, deps（惰性 import win32com）
image_convert   ← utils
word_convert    ← com_core, utils, deps
excel_convert   ← com_core, utils, deps
merge           ← utils, deps
cli             ← 所有模块
```

单向无循环。底层模块从不引用高层模块。

## 关键设计决策

### 决策 1：全局标志 — 模块级变量 + cli 注入

`_force_overwrite` 和 `_allow_kill_office` 定义在 `utils.py` 模块顶部。对外暴露 setter：
- `set_force_overwrite(value: bool) -> None`
- `set_allow_kill_office(value: bool) -> None`

`cli.py` 的 `main()` 解析参数后调用 setter 注入。需要读标志的模块（`utils.py` 的 `_check_overwrite`、`com_core.py` 的 `_com_quit`）直接从 `utils` 读取全局变量。

### 决策 2：COM 模块惰性导入

`com_core.py` 顶层不 import win32com。只在首次需要 Dispatch/DispatchEx/pythoncom 时才 import。确保无 Office 的用户处理图片时不会因缺少 pywin32 而无法启动。

### 决策 3：包内用相对导入

`pdfgj/` 内部模块之间使用 `from .xxx import yyy`。仅在外部入口 `PDFgj.py` 用绝对导入 `from pdfgj.cli import main`。

### 决策 4：兼容旧入口

`PDFgj.py` 保留在项目根目录，3 行代码转发到 `pdfgj.cli.main()`。用户仍然可以 `python PDFgj.py -w`。

## 每个模块的具体内容

### `constants.py`
- `IMG_FORMATS`、`WORD_FORMATS`、`EXCEL_FORMATS`
- 所有 COM 常量（`WD_FORMAT_PDF`、`XL_TYPE_PDF` 等）
- 微软文档参考注释保留

### `deps.py`
- pypdf 三层回退导入逻辑（pypdf → PyPDF2 >=2.0 → PyPDF2 <2.0）
- win32com 检测
- 导出：`_has_pypdf`、`_pypdf_source`、`PdfMerger`、`PdfReader`、`PdfWriter`
- 导出：`_has_win32`、`Dispatch`、`DispatchEx`、`pythoncom`、`pywintypes`

### `utils.py`
- `natural_sort_key()`
- `_get_files()`
- `_progress_bar()`
- 全局标志 `_force_overwrite`、`_allow_kill_office` 及其 setter
- `_check_overwrite()`

### `com_core.py`
- `_COM_PROCESS_NAMES`
- `_get_com_pid()`
- `_com_quit()`
- `_is_com_error()`
- `_classify_com_error()`
- `_precheck_file()`
- `_batch_convert()`
- win32com 惰性导入（函数内 import）

### `image_convert.py`
- `image_to_pdf()`

### `word_convert.py`
- `_setup_word()`
- `_convert_word()`
- `word_to_pdf()`（单文件快捷模式）
- `WordConverter`（上下文管理器，批量模式）

### `excel_convert.py`
- `_setup_excel()`
- `_convert_excel()`
- `excel_to_pdf()`（单文件快捷模式）
- `ExcelConverter`（上下文管理器，批量模式）

### `merge.py`
- `_get_all_pdfs()`
- `merge_pdfs()`

### `cli.py`
- `parse_args()`
- `_print_summary()`
- `main()`

### `__init__.py`
- 重新导出所有公开 API（`WordConverter`、`ExcelConverter`、`image_to_pdf`、`word_to_pdf`、`excel_to_pdf`、`merge_pdfs`、格式常量）

### `__main__.py`
- 一行调用 `main()`

### 根目录 `PDFgj.py`
- 三行薄入口

## 风险清单

| 风险 | 缓解措施 |
|------|---------|
| 循环导入 | 严格遵循依赖方向，实现前画出 import 图再动手 |
| 全局标志时机 | `__init__.py` 只做导入声明，不做实际调用；setter 在 main() 中最早执行 |
| win32com 缺失阻断 | com_core.py 惰性导入，函数内部 import win32com |
| 外部 import 断裂 | 已确认无外部脚本依赖 PDFgj 的 import；`PDFgj.py` 自身保持可用 |
| 相对导入路径 | 包内统一用 `from .xxx import`，避免绝对路径带来的可移植问题 |

## 不在本次范围

- 添加新功能
- 编写单元测试
- 修改业务逻辑
- 发布到 PyPI
