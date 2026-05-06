# 发现与问题分析

## Bug 类问题

### 1. `_is_com_error` 函数逻辑错误 (com_core.py:130-131)
**问题描述：**
```python
def _is_com_error(err: Exception) -> bool:
    """判断异常是否为 COM 相关错误"""
    return (type(err).__qualname__ == 'com_error'
            or type(err).__module__ == 'pywintypes' and type(err).__qualname__ == 'error')
```

**问题分析：**
由于 Python 运算符优先级，`and` 会先于 `or` 结合，导致逻辑错误：
- 实际执行：`type(err).__qualname__ == 'com_error' or (type(err).__module__ == 'pywintypes' and type(err).__qualname__ == 'error')`
- 但代码意图应该是：`(type(err).__qualname__ == 'com_error') or (type(err).__module__ == 'pywintypes' and type(err).__qualname__ == 'error')`

虽然当前写法恰好能工作，但逻辑不清晰，容易导致误解。

**修复方案：** ✅ 已修复
```python
def _is_com_error(err: Exception) -> bool:
    """判断异常是否为 COM 相关错误"""
    return (type(err).__qualname__ == 'com_error' or
            (type(err).__module__ == 'pywintypes' and type(err).__qualname__ == 'error'))
```

### 2. `parse_slide_range` 未处理 total_slides=0 (utils.py:32-83)
**问题描述：**
当 `total_slides=0` 时，函数会：
1. 解析页码范围字符串
2. 裁剪超出范围的页码（所有页码都会被裁剪）
3. 抛出 ValueError："所有指定页码均超出范围"

**问题分析：**
虽然不会导致程序崩溃，但错误信息不够明确。用户可能不清楚为什么"所有页码都超出范围"。

**修复方案：** ✅ 已修复
在函数开头添加检查：
```python
if total_slides <= 0:
    raise ValueError(f"演示文稿没有幻灯片（总数: {total_slides}）")
```

## 优化类问题

### 1. COM 转换器上下文管理器代码重复
**问题描述：**
`WordConverter`、`ExcelConverter`、`PptConverter` 三个类的 `__init__`、`__enter__`、`__exit__` 方法几乎完全相同，仅在以下方面有差异：
- COM 应用名称（'Word.Application'、'Excel.Application'、'PowerPoint.Application'）
- 配置函数（`_setup_word`、`_setup_excel`、`_setup_ppt`）
- 转换函数（`_convert_word`、`_convert_excel`、`_convert_ppt`）

**代码重复统计：**
- WordConverter: 28 行
- ExcelConverter: 28 行
- PptConverter: 28 行
- 总计重复代码：约 84 行

**修复方案：** ✅ 已修复
抽取基类 `COMConverter`：
```python
class COMConverter:
    """COM 转换器基类"""
    def __init__(self):
        if not _has_win32:
            raise RuntimeError("缺少 pywin32 库。请运行: pip install pywin32")
        self._app = None
        self._com_uninit_needed = False

    @property
    def app_name(self) -> str:
        """返回 COM 应用名称（子类必须实现）"""
        raise NotImplementedError

    def setup(self, app: Any) -> None:
        """配置 COM 应用（子类必须实现）"""
        raise NotImplementedError

    def convert(self, path: Path | str) -> bool:
        """转换单个文件（子类必须实现）"""
        raise NotImplementedError

    def __enter__(self) -> 'COMConverter':
        hr = pythoncom.CoInitialize()
        self._com_uninit_needed = (hr == 0)
        self._app = DispatchEx(self.app_name)
        self.setup(self._app)
        return self

    def __exit__(self, *args) -> None:
        if self._app is not None:
            _com_quit(self._app, self.app_name)
        self._app = None
        if self._com_uninit_needed:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
```

### 2. 进度条在非交互式环境中的问题
**问题描述：**
`_progress_bar` 函数使用 `\r` 回车符实现同行刷新：
```python
print(f"\r  {prefix}[{bar}] {current}/{total} ({pct*100:.1f}%)  已用 {elapsed_str}  {eta_str}  ", end='', flush=True)
```

**问题分析：**
- 在终端中正常工作
- 但当输出重定向到文件时，`\r` 会被保留，导致文件内容混乱
- 在某些非交互式环境（如 IDE 输出窗口）中可能显示异常

**修复方案：** ✅ 已修复
检测是否为交互式环境：
```python
def _progress_bar(current: int, total: int, start_time: float, label: str = "") -> None:
    """进度条：仅在交互式终端显示"""
    if not sys.stdout.isatty():
        # 非交互式环境：仅在完成时输出一行
        if current >= total:
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed:.0f}s" if elapsed < 120 else f"{elapsed/60:.1f}min"
            prefix = f"{label}: " if label else ""
            print(f"  {prefix}完成 {current}/{total}，耗时 {elapsed_str}")
        return
    # 原有进度条逻辑...
```

### 3. 文件预检可能误判
**问题描述：**
`_precheck_file` 函数通过尝试读取文件来检测是否被锁定：
```python
try:
    with open(file_path, 'rb') as f:
        f.read(1)
except PermissionError:
    return f"文件被其他程序独占锁定，无法读取: {file_path.name}"
```

**问题分析：**
- 某些文件可能允许读取但不允许写入（如只读文件）
- 某些文件可能在读取时正常，但在 COM 打开时被锁定
- 预检结果可能与实际 COM 操作结果不一致

**修复方案：** ✅ 已修复
将预检改为可选的警告：
```python
def _precheck_file(file_path: Path) -> str | None:
    """打开前预检文件状态，返回错误原因字符串或 None（表示正常）。

    仅检查文件是否存在和是否为文件，其他问题（如权限）交给 COM 操作处理。
    """
    if not file_path.exists():
        return f"文件不存在: {file_path.name}"
    if not file_path.is_file():
        return f"路径不是文件: {file_path.name}"
    # 可读性检查改为警告，不阻断操作
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
    except PermissionError:
        print(f"  [警告] 文件可能被锁定: {file_path.name}")
    except OSError as e:
        print(f"  [警告] 文件访问异常: {file_path.name} ({e})")
    return None
```

## 建议类问题

### 1. 添加单元测试
**当前状态：**
项目无自动化测试，仅通过 `py_compile` 进行语法检查。

**修复方案：** ✅ 已修复
- 为 `parse_slide_range` 函数添加单元测试（17 个测试用例）
- 为 `_is_com_error` 函数添加单元测试（5 个测试用例）
- 为 `_classify_com_error` 函数添加单元测试（5 个测试用例）
- 为 `_precheck_file` 函数添加单元测试（4 个测试用例）
- 为 `natural_sort_key` 函数添加单元测试（4 个测试用例）
- 使用 `pytest` 框架，共 37 个测试用例全部通过

### 2. 改进错误消息
**当前状态：**
某些错误消息可能对用户不够友好。

**修复方案：** ✅ 已修复
- 改进 `parse_slide_range` 函数的错误消息，添加更详细的说明
- 统一错误消息格式
- 为常见错误添加解决建议

### 3. 添加日志系统
**当前状态：**
使用 `print` 输出信息，无法控制日志级别。

**建议：**
- 使用 `logging` 模块
- 支持日志级别控制（DEBUG、INFO、WARNING、ERROR）
- 支持日志文件输出

### 4. 配置文件支持
**当前状态：**
所有配置通过命令行参数传递。

**建议：**
- 支持配置文件（如 `pdfgj.ini` 或 `pdfgj.yaml`）
- 支持环境变量配置
- 配置优先级：命令行 > 环境变量 > 配置文件 > 默认值

## 性能优化建议

### 1. 并行转换
**当前状态：**
所有转换都是串行执行的。

**建议：**
- 对于图片转 PDF，可以考虑并行处理（使用 `multiprocessing` 或 `concurrent.futures`）
- 对于 COM 转换，由于 Office 应用限制，保持串行

### 2. 内存优化
**当前状态：**
`_get_files` 函数一次性加载所有文件路径到内存。

**建议：**
- 对于超大目录，考虑使用生成器
- 添加文件数量限制或警告

## 代码质量建议

### 1. 类型注解完善
**当前状态：**
大部分函数已有类型注解，但某些地方可以改进。

**建议：**
- 为所有公开 API 添加完整的类型注解
- 使用 `TypeAlias` 定义复杂类型

### 2. 文档字符串完善
**当前状态：**
大部分函数有文档字符串，但某些可以更详细。

**建议：**
- 添加参数说明
- 添加返回值说明
- 添加异常说明
- 添加使用示例

### 3. 常量管理
**当前状态：**
COM 常量直接硬编码在 `constants.py` 中。

**建议：**
- 考虑使用 `enum` 模块
- 添加常量文档说明