"""deps 模块的单元测试"""

import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDeps:
    """deps 模块的测试类"""

    def test_has_pypdf(self):
        """测试 pypdf 检测"""
        from pdfgj.deps import _has_pypdf
        # 项目应该安装了 pypdf
        assert _has_pypdf is True

    def test_pypdf_source(self):
        """测试 pypdf 来源"""
        from pdfgj.deps import _pypdf_source
        # 应该是 pypdf
        assert _pypdf_source == 'pypdf'

    def test_has_win32(self):
        """测试 win32 检测"""
        from pdfgj.deps import _has_win32
        # Windows 平台应该有 win32
        import sys
        if sys.platform == 'win32':
            assert _has_win32 is True
        else:
            assert _has_win32 is False

    def test_pdf_reader_import(self):
        """测试 PdfReader 导入"""
        from pdfgj.deps import PdfReader
        assert PdfReader is not None

    def test_pdf_writer_import(self):
        """测试 PdfWriter 导入"""
        from pdfgj.deps import PdfWriter
        assert PdfWriter is not None

    def test_pdf_writer_import(self):
        """测试 PdfWriter 导入"""
        from pdfgj.deps import PdfWriter
        assert PdfWriter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
