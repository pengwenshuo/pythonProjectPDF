"""pypdf / win32com 依赖检测"""

# ============================================================
# pypdf 三层回退导入（pypdf → PyPDF2 >=2.0 → PyPDF2 <2.0）
# ============================================================
try:
    from pypdf import PdfMerger, PdfReader, PdfWriter  # noqa: F811
    _has_pypdf: bool = True
    _pypdf_source: str = 'pypdf'
except ImportError:
    try:
        from PyPDF2 import PdfMerger, PdfReader, PdfWriter  # type: ignore[no-redef]
        _has_pypdf = True
        _pypdf_source = 'PyPDF2 (>=2.0)'
        print("  [提示] 检测到 PyPDF2，建议升级到 pypdf: pip install pypdf")
    except ImportError:
        try:
            from PyPDF2 import PdfMerger, PdfFileReader as PdfReader, PdfFileWriter as PdfWriter  # type: ignore[no-redef]
            _has_pypdf = True
            _pypdf_source = 'PyPDF2 (<2.0，旧版)'
            print("  [提示] 检测到旧版 PyPDF2，建议升级: pip install pypdf")
        except ImportError:
            _has_pypdf = False
            _pypdf_source = ''
            PdfMerger = None  # type: ignore[assignment]
            PdfReader = None  # type: ignore[assignment]
            PdfWriter = None  # type: ignore[assignment]

# ============================================================
# win32com 检测
# ============================================================
try:
    from win32com.client import Dispatch, DispatchEx  # noqa: F811
    import pywintypes
    import pythoncom
    _has_win32: bool = True
except ImportError:
    _has_win32 = False
    Dispatch = None  # type: ignore[assignment]
    DispatchEx = None  # type: ignore[assignment]
    pythoncom = None  # type: ignore[assignment]
