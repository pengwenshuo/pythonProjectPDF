"""Word 转 PDF（需要安装 Word 和 pywin32）"""

import traceback
from pathlib import Path
from typing import Any

from .constants import WD_FORMAT_PDF, WD_DO_NOT_SAVE_CHANGES, WD_ALERTS_NONE, MSO_AUTOMATION_SECURITY_FORCE_DISABLE
from .deps import DispatchEx, pythoncom, _has_win32
from .utils import _check_overwrite
from .com_core import _com_quit, _is_com_error, _classify_com_error, _precheck_file


def _setup_word(word: Any) -> None:
    """配置 Word 应用：禁用弹窗、宏、链接更新"""
    word.Visible = False
    word.DisplayAlerts = WD_ALERTS_NONE
    word.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    try:
        print(f"  [信息] Word 版本: {word.Version} (COM 常量 wdFormatPDF={WD_FORMAT_PDF})")
    except Exception:
        pass  # 版本信息仅用于诊断，失败不影响主流程


def _convert_word(word: Any, word_path: Path) -> bool:
    """使用已启动的 Word 实例转换单个文档（嵌套 try-finally 确保文档关闭）"""
    pdf_path = word_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False

    # 文件状态预检
    pre_err = _precheck_file(word_path)
    if pre_err:
        print(f"  [失败] {pre_err}")
        return False

    doc = None
    try:
        doc = word.Documents.Open(str(word_path.absolute()), ReadOnly=True)
        if doc is None:
            print(f"  [失败] {word_path.name}: 文件无法打开（可能已损坏或设置了打开密码）")
            return False
        doc.SaveAs(str(pdf_path.absolute()), FileFormat=WD_FORMAT_PDF)
        print(f"  [OK] {word_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        if _is_com_error(err):
            reason = _classify_com_error(err)
            print(f"  [失败] {word_path.name}: {reason}")
        else:
            print(f"  [失败] {word_path.name}: {err}")
            traceback.print_exc()
        return False
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE_CHANGES)
            except Exception as e:
                print(f"  [警告] 文档关闭失败: {word_path.name}: {e}")


def word_to_pdf(word_path: Path) -> bool:
    """单文件模式：启动 Word → 转换 → 退出（兼容独立调用）"""
    if not _has_win32:
        print("  [跳过] 缺少 pywin32 库，无法转换 Word。请运行: pip install pywin32")
        return False
    word = None
    try:
        word = DispatchEx('Word.Application')
        _setup_word(word)
        return _convert_word(word, word_path)
    finally:
        _com_quit(word, 'Word.Application')


class WordConverter:
    """
    Word 转 PDF 上下文管理器，复用同一 Application 实例批量转换。

    用法:
        with WordConverter() as wc:
            wc.convert('a.docx')
            wc.convert('b.docx')
    """
    def __init__(self) -> None:
        if not _has_win32:
            raise RuntimeError("缺少 pywin32 库。请运行: pip install pywin32")
        self._app = None
        self._com_uninit_needed: bool = False

    def __enter__(self) -> 'WordConverter':
        hr = pythoncom.CoInitialize()  # type: ignore[union-attr]
        # S_OK(0)=成功需要Uninit, S_FALSE(1)=已初始化不需要, 其他=失败
        self._com_uninit_needed = (hr == 0)
        self._app = DispatchEx('Word.Application')
        _setup_word(self._app)
        return self

    def __exit__(self, *args) -> None:
        if self._app is not None:
            _com_quit(self._app, 'Word.Application')
        self._app = None
        if self._com_uninit_needed:
            try:
                pythoncom.CoUninitialize()  # type: ignore[union-attr]
            except Exception:
                pass

    def convert(self, path: Path | str) -> bool:
        """转换单个 Word 文档为 PDF（复用当前 Application 实例）"""
        return _convert_word(self._app, Path(path))
