# 任务计划：PPT 转 PDF 功能

## 目标
按照 `docs/superpowers/specs/2026-05-05-ppt-to-pdf-design.md` 设计规范，为 PDFgj 添加 PowerPoint 演示文稿转 PDF 功能。

## 当前阶段
全部完成

## 各阶段

### 阶段 1：常量与进程映射
- [x] `constants.py` 添加 `PPT_FORMATS`、`PP_SAVE_AS_PDF`、`PP_PRINT_RANGE_ALL`、`PP_PRINT_RANGE_SLIDES`
- [x] `com_core.py` 添加 `PowerPoint.Application → POWERPNT.EXE` 映射
- [x] `com_core.py` 的 `_classify_com_error()` 添加 PPT 特有 HRESULT
- **状态：** complete

### 阶段 2：页码范围解析
- [x] `utils.py` 添加 `parse_slide_range()` 函数
- **状态：** complete

### 阶段 3：PPT 转换器
- [x] 新建 `ppt_convert.py`（_setup_ppt、_convert_ppt、_export_slides、ppt_to_pdf、PptConverter）
- **状态：** complete

### 阶段 4：CLI 集成
- [x] `cli.py` 添加 `-p/--ppt` 互斥参数
- [x] `cli.py` 添加 `--slides` 参数 + 校验逻辑
- [x] `cli.py` 添加 PPT 主流程分支
- [x] `cli.py` 更新帮助文本
- **状态：** complete

### 阶段 5：验证
- [x] 语法检查所有模块（13/13 通过）
- [x] `python -m pdfgj -h` 验证帮助文本
- [x] `python -m pdfgj --slides 1,3,5-8` 验证参数校验
- **状态：** complete

## 关键决策
| 决策 | 理由 |
|------|------|
| 复用现有 COM 转换器模式 | 3 个转换器重复代码量可控，不需抽取基类 |
| --slides 参数与 -p 绑定 | 与 --output 仅在 -m 下有效的校验逻辑一致 |
| PptConverter 构造函数接收 slides | 批量转换时所有文件共享同一页码范围 |

## 设计文档
`docs/superpowers/specs/2026-05-05-ppt-to-pdf-design.md`
