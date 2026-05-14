"""PDF处理器单元测试"""

import pytest
from pathlib import Path
from pdfgj.pdf_processor import PDFProcessor


@pytest.fixture
def processor():
    """创建PDF处理器实例"""
    return PDFProcessor()


class TestPDFProcessorInit:
    """PDF处理器初始化测试"""

    def test_init_success(self):
        """测试正常初始化"""
        processor = PDFProcessor()
        assert processor is not None
        assert processor.A4_WIDTH == 595.28
        assert processor.A4_HEIGHT == 841.89


class TestValidateFile:
    """文件验证测试"""

    def test_validate_empty_file(self, processor, tmp_path):
        """测试空文件（0字节）"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        is_valid, error_msg = processor.validate_file(empty_file)
        assert is_valid is False
        assert "文件为空" in error_msg

    def test_validate_invalid_pdf(self, processor, tmp_path):
        """测试无效的PDF文件"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        is_valid, error_msg = processor.validate_file(invalid_file)
        assert is_valid is False
        assert "无法打开PDF" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
