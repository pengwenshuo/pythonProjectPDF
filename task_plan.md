# 任务计划：PDFgj.py 模块化重构（第三轮）

## 目标
按照 `docs/superpowers/specs/2026-05-01-pdfgj-refactor-design.md` 设计规范，将 781 行 `PDFgj.py` 拆分为 `pdfgj/` 包（11 模块 + 根入口）。

## 当前阶段
全部完成

## 各阶段

### 阶段 1：创建包骨架
- [x] 创建 `pdfgj/` 目录
- [x] 创建 `constants.py`（零依赖，格式常量 + COM 常量）
- [x] 创建 `deps.py`（pypdf/Win32COM 依赖检测）
- **状态：** complete

### 阶段 2：工具层
- [x] 创建 `utils.py`（排序、文件获取、进度条、覆盖保护、全局标志 + setter）
- **状态：** complete

### 阶段 3：COM 公共层
- [x] 创建 `com_core.py`（PID 获取、进程退出、错误分类、预检、批量转换，win32com 惰性导入）
- **状态：** complete

### 阶段 4：业务层（转换器）
- [x] 创建 `image_convert.py`
- [x] 创建 `word_convert.py`
- [x] 创建 `excel_convert.py`
- [x] 创建 `merge.py`
- **状态：** complete

### 阶段 5：CLI 层 + 入口
- [x] 创建 `cli.py`（参数解析 + main）
- [x] 创建 `__init__.py`（公开 API 重新导出）
- [x] 创建 `__main__.py`
- [x] 重写 `PDFgj.py` 为薄入口
- **状态：** complete

### 阶段 6：验证与清理
- [x] 语法检查所有 12 模块 → 全部通过
- [x] `python PDFgj.py -h` 可用性测试 → 通过
- [x] `python -m pdfgj -h` 可用性测试 → 通过
- **状态：** complete

## 关键决策
| 决策 | 理由 |
|------|------|
| 自下而上创建 | 每次只引入已验证的下层模块 |
| 包内用相对 import | 可移植，避免绝对路径问题 |
| com_core 惰性 import win32com | 无 Office 用户处理图片不报错 |
| 全局标志放 utils.py + `from . import utils` 引用 | 避免模块级别直接 import 导致值快照问题 |

## 模块统计

| 文件 | 行数 | 职责 |
|------|------|------|
| constants.py | 20 | 格式常量 + COM 常量 |
| deps.py | 37 | pypdf 三层回退 + Win32COM 检测 |
| utils.py | 73 | 排序、文件获取、进度条、覆盖保护、全局标志 |
| com_core.py | 160 | PID 获取、进程退出、错误分类、预检、批量转换 |
| image_convert.py | 27 | 图片转 PDF |
| word_convert.py | 85 | Word 配置、转换、单文件模式、上下文管理器 |
| excel_convert.py | 86 | Excel 配置、转换、单文件模式、上下文管理器 |
| merge.py | 72 | PDF 合并 |
| cli.py | 101 | 参数解析 + 主流程 |
| __init__.py | 10 | 公开 API 导出 |
| __main__.py | 3 | python -m pdfgj 入口 |
| PDFgj.py | 6 | 根入口（兼容旧习惯） |
