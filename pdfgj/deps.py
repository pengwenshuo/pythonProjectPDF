"""pypdf / win32com 依赖检测"""

# ============================================================
# pypdf 导入
# ============================================================
try:
    from pypdf import PdfReader, PdfWriter, PageObject, Transformation  # noqa: F811
    _has_pypdf: bool = True
    _pypdf_source: str = 'pypdf'
except ImportError:
    _has_pypdf = False
    _pypdf_source = ''
    PdfReader = None  # type: ignore[assignment]
    PdfWriter = None  # type: ignore[assignment]
    PageObject = None  # type: ignore[assignment,misc]
    Transformation = None  # type: ignore[assignment,misc]

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
