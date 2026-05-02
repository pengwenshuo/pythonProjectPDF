# 发现与决策

## 模块化重构分析

### 当前状态
- `PDFgj.py` 共 781 行，包含 ~18 个逻辑块
- 结构清晰（有分区注释），但单文件过大不利于协作和维护
- 无其他脚本依赖 PDFgj 的内部 import

### 拆分方案
- **粒度：** 中粒度（10 模块 + 根入口），每文件 30-140 行
- **依赖方向：** constants → deps → utils → com_core → converters(image/word/excel/merge) → cli
- **入口：** 保留 `PDFgj.py` 薄入口 + 新增 `python -m pdfgj`

### 关键决策
| 决策 | 理由 |
|------|------|
| 全局标志放 utils.py + setter 注入 | 避免循环依赖，最小改动 |
| com_core.py 惰性 import win32com | 无 Office 用户处理图片不报错 |
| 包内用相对 import | 可移植，不依赖安装路径 |
| 自下而上创建 | 每步只引入已验证的下层，降低调试难度 |
