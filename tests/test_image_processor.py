"""图片处理器单元测试"""

import pytest
from pathlib import Path
from PIL import Image

from pdfgj.image_processor import ImageProcessor


@pytest.fixture
def processor():
    """创建图片处理器实例"""
    return ImageProcessor()


@pytest.fixture
def create_test_image(tmp_path):
    """创建测试图片的辅助函数"""
    def _create(filename: str, mode: str = 'RGB', size: tuple = (100, 100)):
        filepath = tmp_path / filename
        img = Image.new(mode, size, color='red')
        img.save(filepath)
        return filepath
    return _create


class TestImageProcessorInit:
    """图片处理器初始化测试"""

    def test_init_success(self):
        """测试正常初始化"""
        processor = ImageProcessor()
        assert processor is not None


class TestValidate:
    """文件验证测试"""

    def test_validate_nonexistent_file(self, processor, tmp_path):
        """测试文件不存在"""
        nonexistent = tmp_path / "nonexistent.jpg"
        is_valid, error_msg = processor.validate(nonexistent)
        assert is_valid is False
        assert "文件不存在" in error_msg

    def test_validate_unsupported_format(self, processor, tmp_path):
        """测试不支持的格式"""
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("test")
        is_valid, error_msg = processor.validate(unsupported)
        assert is_valid is False
        assert "不支持的格式" in error_msg

    def test_validate_corrupted_image(self, processor, tmp_path):
        """测试损坏的图片"""
        corrupted = tmp_path / "corrupted.jpg"
        corrupted.write_text("这不是一个图片文件")
        is_valid, error_msg = processor.validate(corrupted)
        assert is_valid is False
        assert "无法打开图片" in error_msg

    def test_validate_valid_image(self, processor, create_test_image):
        """测试正常图片"""
        valid_image = create_test_image("valid.jpg")
        is_valid, error_msg = processor.validate(valid_image)
        assert is_valid is True
        assert error_msg == ""


class TestProcessGif:
    """GIF处理测试"""

    def test_extract_first_frame(self, processor, tmp_path):
        """测试GIF只取第一帧"""
        # 创建多帧GIF
        gif_path = tmp_path / "test.gif"
        frames = []
        for i in range(5):
            frame = Image.new('RGB', (100, 100), color=(i * 50, 0, 0))
            frames.append(frame)
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )

        # 处理GIF
        result = processor.process(gif_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()


class TestFixExifOrientation:
    """EXIF方向矫正测试"""

    def test_exif_no_rotation(self, processor, create_test_image):
        """测试无EXIF旋转"""
        img_path = create_test_image("no_exif.jpg")
        img = Image.open(img_path)
        result = processor._fix_exif_orientation(img)
        assert result.size == (100, 100)
        result.close()

    def test_exif_rotation_handling(self, processor, tmp_path):
        """测试EXIF旋转处理"""
        # 创建带EXIF旋转的图片
        img_path = tmp_path / "exif_rotate.jpg"
        img = Image.new('RGB', (200, 100), color='blue')

        # 添加EXIF方向信息（旋转90度）
        exif_data = img.getexif()
        exif_data[0x0112] = 6  # 6表示旋转90度
        img.save(img_path, exif=exif_data.tobytes())

        # 处理图片
        result = processor.process(img_path)
        assert result is not None
        # 旋转90度后，宽高应该交换
        assert result.size == (100, 200)
        result.close()


class TestNormalizeMode:
    """格式转换测试"""

    def test_rgba_to_rgb(self, processor, create_test_image):
        """测试RGBA转RGB"""
        img_path = create_test_image("rgba.png", mode='RGBA')
        img = Image.open(img_path)
        result = processor._normalize_mode(img)
        assert result.mode == 'RGB'
        result.close()

    def test_palette_to_rgb(self, processor, tmp_path):
        """测试P模式转RGB"""
        # 创建P模式图片
        img_path = tmp_path / "palette.png"
        img = Image.new('P', (100, 100))
        img.save(img_path)

        img = Image.open(img_path)
        result = processor._normalize_mode(img)
        assert result.mode == 'RGB'
        result.close()

    def test_rgb_unchanged(self, processor, create_test_image):
        """测试RGB不变"""
        img_path = create_test_image("rgb.jpg", mode='RGB')
        img = Image.open(img_path)
        result = processor._normalize_mode(img)
        assert result.mode == 'RGB'
        assert result.size == (100, 100)
        result.close()


class TestProcess:
    """process方法集成测试"""

    def test_process_valid_image(self, processor, create_test_image):
        """测试处理正常图片"""
        img_path = create_test_image("valid.jpg")
        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_nonexistent_image(self, processor, tmp_path):
        """测试处理不存在的图片"""
        nonexistent = tmp_path / "nonexistent.jpg"
        result = processor.process(nonexistent)
        assert result is None

    def test_process_corrupted_image(self, processor, tmp_path):
        """测试处理损坏的图片"""
        corrupted = tmp_path / "corrupted.jpg"
        corrupted.write_text("这不是一个图片文件")
        result = processor.process(corrupted)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
