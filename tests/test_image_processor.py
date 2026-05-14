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

    def test_l_mode_to_rgb(self, processor, create_test_image):
        """测试L模式转RGB"""
        img_path = create_test_image("grayscale.jpg", mode='L')
        img = Image.open(img_path)
        result = processor._normalize_mode(img)
        assert result.mode == 'RGB'
        result.close()


class TestExtractGifFrame:
    """_extract_gif_frame 方法测试"""

    def test_extract_first_frame(self, processor, tmp_path):
        """测试提取GIF第一帧"""
        gif_path = tmp_path / "test.gif"
        frames = []
        for i in range(3):
            frame = Image.new('RGB', (100, 100), color=(i * 80, 0, 0))
            frames.append(frame)
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )

        img = Image.open(gif_path)
        result = processor._extract_gif_frame(img)
        assert result is not None
        assert result.mode in ('RGB', 'RGBA', 'P')
        result.close()


class TestFixExifOrientation:
    """_fix_exif_orientation 方法测试"""

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

    def test_process_rgba_image(self, processor, create_test_image):
        """测试处理RGBA图片"""
        img_path = create_test_image("rgba.png", mode='RGBA')
        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_palette_image(self, processor, tmp_path):
        """测试处理调色板模式图片"""
        img_path = tmp_path / "palette.png"
        img = Image.new('P', (100, 100))
        img.save(img_path)

        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_gif_image(self, processor, tmp_path):
        """测试处理GIF图片"""
        gif_path = tmp_path / "test.gif"
        frames = []
        for i in range(3):
            frame = Image.new('RGB', (100, 100), color=(i * 80, 0, 0))
            frames.append(frame)
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )

        result = processor.process(gif_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_webp_image(self, processor, create_test_image):
        """测试处理WebP图片"""
        img_path = create_test_image("test.webp")
        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_bmp_image(self, processor, create_test_image):
        """测试处理BMP图片"""
        img_path = create_test_image("test.bmp")
        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_tiff_image(self, processor, create_test_image):
        """测试处理TIFF图片"""
        img_path = create_test_image("test.tiff")
        result = processor.process(img_path)
        assert result is not None
        assert result.mode == 'RGB'
        result.close()

    def test_process_memory_error(self, processor, create_test_image, monkeypatch):
        """测试内存不足"""
        img_path = create_test_image("valid.jpg")

        original_open = Image.open

        def mock_open(*args, **kwargs):
            img = original_open(*args, **kwargs)
            original_save = img.save

            def raise_memory(*a, **kw):
                raise MemoryError()
            # 让后续操作触发内存错误
            return img

        # 让 _normalize_mode 触发 MemoryError
        original_normalize = processor._normalize_mode

        def mock_normalize(img):
            raise MemoryError()

        monkeypatch.setattr(processor, '_normalize_mode', mock_normalize)
        result = processor.process(img_path)
        assert result is None

    def test_process_general_exception(self, processor, create_test_image, monkeypatch):
        """测试一般处理异常"""
        img_path = create_test_image("valid.jpg")

        original_normalize = processor._normalize_mode

        def mock_normalize(img):
            raise RuntimeError("test error")

        monkeypatch.setattr(processor, '_normalize_mode', mock_normalize)
        result = processor.process(img_path)
        assert result is None

    def test_process_open_exception(self, processor, create_test_image, monkeypatch):
        """测试 Image.open 异常"""
        img_path = create_test_image("valid.jpg")

        original_open = Image.open

        def mock_open(*args, **kwargs):
            raise IOError("open error")

        monkeypatch.setattr(Image, 'open', mock_open)
        result = processor.process(img_path)
        assert result is None

    def test_fix_exif_orientation_exception(self, processor, create_test_image, monkeypatch):
        """测试 EXIF 矫正异常"""
        from PIL import ImageOps as _ImageOps
        img_path = create_test_image("valid.jpg")

        def mock_transpose(img):
            raise Exception("exif error")

        monkeypatch.setattr(_ImageOps, 'exif_transpose', mock_transpose)
        result = processor.process(img_path)
        assert result is not None  # 异常时返回原图


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
