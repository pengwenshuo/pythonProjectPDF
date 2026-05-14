# 任务计划：图片转PDF功能改进

## 目标
改进图片转PDF功能，解决GIF处理异常、EXIF方向未矫正、图片未验证等缺陷，提升稳定性和用户体验。

## 设计文档
docs/superpowers/specs/2026-05-14-image-convert-improvement-design.md

## 当前阶段
全部完成

## 各阶段

### 阶段 1：创建图片处理器模块
- [x] 创建 pdfgj/image_processor.py 文件
- [x] 实现 ImageProcessor 类
- [x] 实现 validate() 方法（文件存在性、格式支持、可读性检查）
- [x] 实现 _fix_exif_orientation() 方法（读取EXIF方向标记，自动旋转）
- [x] 实现 _extract_gif_frame() 方法（提取GIF第一帧）
- [x] 实现 _normalize_mode() 方法（RGBA/P → RGB，白底填充）
- [x] 实现 process() 方法（串联所有预处理步骤）
- **状态：** complete

### 阶段 2：重构 image_convert.py
- [x] 修改 image_to_pdf() 函数，调用 ImageProcessor
- [x] 移除原有的内联预处理代码
- [x] 添加 finally 块确保图片资源释放
- [x] 保持函数接口不变（向后兼容）
- **状态：** complete

### 阶段 3：编写单元测试
- [x] 创建 tests/test_image_processor.py 文件
- [x] 实现 TestImageProcessorInit 测试类
- [x] 实现 TestValidate 测试类（4个用例）
- [x] 实现 TestProcessGif 测试类（1个用例）
- [x] 实现 TestFixExifOrientation 测试类（2个用例）
- [x] 实现 TestNormalizeMode 测试类（3个用例）
- [x] 运行所有测试确保通过
- **状态：** complete

### 阶段 4：验证与文档更新
- [x] 语法检查所有模块
- [x] 运行单元测试
- [x] 更新 task_plan.md
- [x] 更新 progress.md
- [x] 更新 findings.md
- **状态：** complete

## 关键问题
1. Pillow 的 EXIF 方向读取方式？✅ 使用 ImageOps.exif_transpose()
2. GIF 只取第一帧如何实现？✅ 使用 img.seek(0)
3. 如何处理损坏的图片文件？✅ 捕获异常，返回 None

## 已做决策
| 决策 | 理由 |
|------|------|
| 创建独立的 image_processor.py 模块 | 职责分离，代码清晰，可维护性好 |
| 使用 ImageOps.exif_transpose() 处理EXIF | Pillow 内置方法，简洁可靠 |
| GIF 只取第一帧 | 避免生成巨大PDF文件 |
| 逐张处理，处理完释放 | 控制内存占用 |
| 跳过并报告损坏图片 | 不中断批量处理流程 |

## 遇到的错误
| 错误 | 尝试次数 | 解决方案 |
|------|---------|---------|
| 资源泄漏：中间图像未关闭 | 1 | 在 process() 中统一管理图像生命周期 |
| GIF异常处理可能返回损坏图像 | 1 | 失败时尝试重新打开图像 |

## 备注
- 参考设计文档：docs/superpowers/specs/2026-05-14-image-convert-improvement-design.md
- Pillow 已安装在虚拟环境（版本12.2.0）
- 所有文档和用户界面使用简体中文
