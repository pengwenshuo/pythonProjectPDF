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


class TestProcessPdf:
    """process_pdf 方法测试"""

    def test_process_nonexistent_file(self, processor, tmp_path):
        """测试处理不存在的文件"""
        nonexistent = tmp_path / "nonexistent.pdf"
        # 不存在的文件会抛出 FileNotFoundError
        with pytest.raises(FileNotFoundError):
            processor.process_pdf(nonexistent)

    def test_process_invalid_file(self, processor, tmp_path):
        """测试处理无效文件"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        success, pages, error_msg = processor.process_pdf(invalid_file)
        assert success is False
        assert pages == []
        assert "无法打开PDF" in error_msg

    def test_process_empty_file(self, processor, tmp_path):
        """测试处理空文件"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        success, pages, error_msg = processor.process_pdf(empty_file)
        assert success is False
        assert pages == []
        assert "文件为空" in error_msg


class TestValidateFile:
    """validate_file 方法测试"""

    def test_validate_empty_file(self, processor, tmp_path):
        """测试空文件"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        is_valid, error_msg = processor.validate_file(empty_file)
        assert is_valid is False
        assert "文件为空" in error_msg

    def test_validate_invalid_pdf(self, processor, tmp_path):
        """测试无效PDF"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        is_valid, error_msg = processor.validate_file(invalid_file)
        assert is_valid is False
        assert "无法打开PDF" in error_msg


class TestStandardizePage:
    """standardize_page 方法测试"""

    def test_standardize_page_dimensions(self, processor, tmp_path):
        """测试页面标准化尺寸"""
        from pypdf import PdfWriter, PdfReader

        # 创建一个非A4尺寸的PDF
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=400)
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        reader = PdfReader(str(pdf_path))
        page = reader.pages[0]

        # 标准化到A4
        new_page = processor.standardize_page(page)

        # 验证新页面尺寸接近A4
        width = float(new_page.mediabox.width)
        height = float(new_page.mediabox.height)
        assert abs(width - 595.28) < 1
        assert abs(height - 841.89) < 1


class TestCorrectOrientation:
    """correct_orientation 方法测试"""

    def test_no_rotation(self, processor, tmp_path):
        """测试无旋转的情况"""
        from pypdf import PdfWriter, PdfReader

        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        reader = PdfReader(str(pdf_path))
        page = reader.pages[0]

        # 无旋转时应返回原页面
        result = processor.correct_orientation(page)
        assert result is page

    def test_rotation_90(self, processor, tmp_path):
        """测试90度旋转"""
        from pypdf import PdfWriter, PdfReader
        from pypdf.generic import NameObject, NumberObject

        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        page = writer.add_blank_page(width=595, height=842)
        # 直接设置 /Rotate 属性
        page[NameObject('/Rotate')] = NumberObject(90)
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        reader = PdfReader(str(pdf_path))
        page = reader.pages[0]

        # 矫正方向后应返回新页面
        result = processor.correct_orientation(page)
        assert result is not page


class TestProcessPdf:
    """process_pdf 方法测试"""

    def test_process_nonexistent_file(self, processor, tmp_path):
        """测试处理不存在的文件"""
        nonexistent = tmp_path / "nonexistent.pdf"
        with pytest.raises(FileNotFoundError):
            processor.process_pdf(nonexistent)

    def test_process_invalid_file(self, processor, tmp_path):
        """测试处理无效文件"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        success, pages, error_msg = processor.process_pdf(invalid_file)
        assert success is False
        assert pages == []
        assert "无法打开PDF" in error_msg

    def test_process_empty_file(self, processor, tmp_path):
        """测试处理空文件"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        success, pages, error_msg = processor.process_pdf(empty_file)
        assert success is False
        assert pages == []
        assert "文件为空" in error_msg

    def test_process_valid_pdf(self, processor, tmp_path):
        """测试处理有效 PDF"""
        from pypdf import PdfWriter

        pdf_path = tmp_path / "valid.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        success, pages, error_msg = processor.process_pdf(pdf_path)
        assert success is True
        assert len(pages) == 1
        assert error_msg == ""


class TestValidateFile:
    """validate_file 方法测试"""

    def test_validate_empty_file(self, processor, tmp_path):
        """测试空文件"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()
        is_valid, error_msg = processor.validate_file(empty_file)
        assert is_valid is False
        assert "文件为空" in error_msg

    def test_validate_invalid_pdf(self, processor, tmp_path):
        """测试无效PDF"""
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("这不是一个PDF文件")
        is_valid, error_msg = processor.validate_file(invalid_file)
        assert is_valid is False
        assert "无法打开PDF" in error_msg

    def test_validate_valid_pdf(self, processor, tmp_path):
        """测试有效 PDF"""
        from pypdf import PdfWriter
        pdf_path = tmp_path / "valid.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        is_valid, error_msg = processor.validate_file(pdf_path)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_no_pages_pdf(self, processor, tmp_path):
        """测试无页面的 PDF"""
        from pypdf import PdfWriter
        pdf_path = tmp_path / "nopages.pdf"
        writer = PdfWriter()
        # 不添加任何页面
        with open(pdf_path, 'wb') as f:
            writer.write(f)

        is_valid, error_msg = processor.validate_file(pdf_path)
        assert is_valid is False
        assert "没有页面" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
