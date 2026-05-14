"""image_convert 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from pdfgj.image_convert import image_to_pdf
from pdfgj.image_processor import ImageProcessor


@pytest.fixture
def create_test_image(tmp_path):
    """创建测试图片的辅助函数"""
    def _create(filename: str, mode: str = 'RGB', size: tuple = (100, 100)):
        filepath = tmp_path / filename
        img = Image.new(mode, size, color='red')
        img.save(filepath)
        return filepath
    return _create


class TestImageToPdf:
    """image_to_pdf 函数的测试类"""

    def test_convert_jpg_to_pdf(self, create_test_image, tmp_path):
        """测试JPG转PDF"""
        img_path = create_test_image("test.jpg")
        result = image_to_pdf(img_path)
        assert result is True
        assert (tmp_path / "test.pdf").exists()

    def test_convert_png_to_pdf(self, create_test_image, tmp_path):
        """测试PNG转PDF"""
        img_path = create_test_image("test.png")
        result = image_to_pdf(img_path)
        assert result is True
        assert (tmp_path / "test.pdf").exists()

    def test_convert_rgba_to_pdf(self, create_test_image, tmp_path):
        """测试RGBA图片转PDF"""
        img_path = create_test_image("test.png", mode='RGBA')
        result = image_to_pdf(img_path)
        assert result is True
        assert (tmp_path / "test.pdf").exists()

    def test_convert_nonexistent_file(self, tmp_path):
        """测试不存在的文件"""
        nonexistent = tmp_path / "nonexistent.jpg"
        result = image_to_pdf(nonexistent)
        assert result is False

    def test_convert_unsupported_format(self, tmp_path):
        """测试不支持的格式"""
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("test")
        result = image_to_pdf(unsupported)
        assert result is False

    def test_convert_corrupted_image(self, tmp_path):
        """测试损坏的图片"""
        corrupted = tmp_path / "corrupted.jpg"
        corrupted.write_text("这不是一个图片文件")
        result = image_to_pdf(corrupted)
        assert result is False

    def test_convert_save_error(self, create_test_image, tmp_path, monkeypatch):
        """测试保存失败"""
        img_path = create_test_image("test.jpg")

        original_save = Image.Image.save

        def mock_save(self, *args, **kwargs):
            if kwargs.get('format') == 'PDF' or (len(args) > 1 and args[1] == 'PDF'):
                raise PermissionError("denied")
            return original_save(self, *args, **kwargs)

        monkeypatch.setattr(Image.Image, 'save', mock_save)
        result = image_to_pdf(img_path)
        assert result is False

    def test_convert_overwrite_rejected(self, create_test_image, tmp_path):
        """测试用户拒绝覆盖"""
        img_path = create_test_image("test.jpg")
        # 先创建一个同名 PDF
        (tmp_path / "test.pdf").touch()

        with patch('pdfgj.image_convert._check_overwrite', return_value=False):
            result = image_to_pdf(img_path)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
