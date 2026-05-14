# CLI 默认模式重构设计

## 目标

将 PDF 合并设为默认模式（无参数时执行），图片转 PDF 改用 `-i` 参数触发，去掉灰度功能。

## 当前状态

| 行为 | 参数 |
|------|------|
| 图片转 PDF（默认） | 无参数 / `-g`（灰度） |
| PDF 合并 | `-m` |
| Word 转 PDF | `-w` |
| Excel 转 PDF | `-e` |
| PPT 转 PDF | `-p` |

## 目标状态

| 行为 | 参数 |
|------|------|
| PDF 合并（默认） | 无参数 |
| 图片转 PDF | `-i` / `--image` |
| Word 转 PDF | `-w`（不变） |
| Excel 转 PDF | `-e`（不变） |
| PPT 转 PDF | `-p`（不变） |

## 变更范围

### 1. `cli.py` — `parse_args()`

- 互斥组中 `-g`/`--gray` 替换为 `-i`/`--image`，help 文本改为"图片模式：图片转 PDF"
- 去掉 `-g`/`--gray` 参数
- 更新 epilog 中的快捷方式示例

### 2. `cli.py` — `main()`

- 将合并分支移到最后作为默认 fallback（去掉 `if args.merge` 的 early return，改为最后的 else 分支）
- 将图片转 PDF 分支改为 `if args.image`
- 去掉 `grayscale=args.gray` 参数传递

### 3. `cli.py` — 参数校验

- `-o`/`--output`/`--sortby` 的校验条件从 `not args.merge` 改为 `not args.merge and not is_default_merge`（默认模式也是合并，需要允许这些参数）

### 4. `image_convert.py`

- `image_to_pdf()` 去掉 `grayscale` 参数
- 删除灰度转换相关逻辑

### 5. 文档更新

- `CLAUDE.md` 更新四种模式的描述
- `pyproject.toml` 或 `setup.py` 中的描述（如有）

## 不变的部分

- `-w`、`-e`、`-p`、`-r`、`-y`、`--kill-office`、`--slides` 均不变
- `merge.py`、`word_convert.py`、`excel_convert.py`、`ppt_convert.py` 均不变
- `constants.py`、`deps.py`、`utils.py`、`com_core.py` 均不变

## 默认模式下的行为

当用户不传任何模式参数时：
1. 尝试在当前目录查找 PDF 文件
2. 如果找到，执行合并（使用 `-o` 和 `--sortby` 的默认值）
3. 如果没找到，打印提示信息
