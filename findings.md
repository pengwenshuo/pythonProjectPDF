# 发现与决策

## PPT 转 PDF 功能

### COM 自动化模式
- Word/Excel 转换器遵循完全相同的结构：_setup → _convert → 单文件函数 → 上下文管理器
- PPT 可直接复用此模式，差异仅在 ExportAsFixedFormat 参数

### PowerPoint ExportAsFixedFormat 关键参数
- `Path=32` (ppSaveAsPDF)
- `RangeType=1` (全部) 或 `RangeType=3` (指定范围)
- 指定范围时需创建 `PrintRanges` 对象

### 页码范围解析
- 格式：`"1,3,5-8"` — 支持单页和范围组合
- 需处理：超出范围裁剪、无效格式报错、空输入

### 进程名映射
- `PowerPoint.Application → POWERPNT.EXE`
- 已有：`Word.Application → WINWORD.EXE`、`Excel.Application → EXCEL.EXE`
